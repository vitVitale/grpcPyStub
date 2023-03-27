import re
from os import environ


print("""
*****************************************
* gRPC-stub generation tool             *
* based on Python 3.10.7                *
* maintained by: vitvasilyuk@gmail.com  *
*****************************************
""")


def substr(rows: list, regex: str, group: int = 0, is_single: bool = True):
    pars = []
    for row in rows:
        result = re.search(pattern=regex, string=row)
        if result is not None:
            try:
                if is_single:
                    return result.group(group)
                else:
                    pars.append((result.group(group), result.group(group+1)))
            except IndexError:
                continue
    if is_single:
        raise Exception(f'В тексте отсутствуют подстроки,\n'
                        f'соответствующие регулярному выражению: {regex}')
    return pars


with open(f"../proto/{environ.get('PROTO_FILE')}", "r", encoding='utf-8') as stream:
    print(f"\nGENERATE_FOR: {environ.get('PROTO_FILE')}\n")
    lines = stream.readlines()

data = {
    "proto_file": environ.get('PROTO_FILE'),
    "service_name": substr(lines, r'service (\w+)', 1),
    "rpc": substr(lines, r'rpc (\w+).+ returns \((\w+)\)', 1, is_single=False)
}

rpcs_str = '\n\t'.join([x[0] for x in data['rpc']])

print(f'''
FindService -> {data['service_name']}
RPCs -> 
    {rpcs_str}
''')

grpc_service_template = """

class {{ service_name }}Dispatcher(services.{{ service_name }}Servicer):
    log = logging.getLogger('{{ service_name }}')
    log.setLevel(logging.INFO)
    log.addHandler(handler)
    vars().update(DTOs)
""".replace('{{ service_name }}', data['service_name'])

grpc_rpc_template = """
    def {{ rpc_name }}(self, request, context):
        {{ service_name }}Dispatcher.log.info(f'INCOMING << {json_logs_converter(request)}')
        reply = fill_answer(marker=f'{{ service_name }}::{currentframe().f_code.co_name}',
                            logger={{ service_name }}Dispatcher.log,
                            base=self.{{ rpc_outgoing_dto }}(),
                            message=request)
        {{ service_name }}Dispatcher.log.info(f'OUTGOING >> {json_logs_converter(reply)}')
        return reply
"""

for rpc_name, out_dto in data['rpc']:
    grpc_service_template += grpc_rpc_template\
        .replace('{{ service_name }}', data['service_name'])\
        .replace('{{ rpc_name }}', rpc_name)\
        .replace('{{ rpc_outgoing_dto }}', out_dto)

grpc_run_server_template = """

def run_grpc_server():
    server = grpc.server(ThreadPoolExecutor(max_workers=NUM_WORKERS))
    services.add_{{ service_name }}Servicer_to_server({{ service_name }}Dispatcher(), server)
    server.add_insecure_port(f'[::]:{GRPC_PORT}')
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(run_grpc_server),
                   executor.submit(uvicorn.run, app=app, host="0.0.0.0", port=REST_PORT)]
        for future in as_completed(futures):
            pass
""".replace('{{ service_name }}', data['service_name'])

stub_file = """import sys
import grpc
import types
import logging
import uvicorn
from os import environ
from fastapi import FastAPI, Request
from json import loads, dumps
from typing import Union
from inspect import currentframe
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.protobuf.json_format import MessageToJson, Parse, MessageToDict

# DTO
sys.path.append('/proto')
proto, services = grpc.protos_and_services("{{ protobuf_name }}")


def _filter_protected_(module):
    return {key: value for key, value in module.__dict__.items()
            if not (key.startswith('__')
                    or key.startswith('_')
                    or key.startswith('add_')
                    or key == 'grpc')}


def _register_grpc_dto_(modules):
    initial: dict = _filter_protected_(modules)
    '''  check if it has modules  '''
    while [i for i in list(initial.values()) if isinstance(i, types.ModuleType)]:
        work: dict = initial.copy()
        for k, v in work.items():
            if isinstance(v, types.ModuleType):
                initial.update(_filter_protected_(initial.pop(k)))
    return initial


handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s :: %(levelname)5s :: %(name)22s :: %(funcName)17s() :: %(message)s')
handler.setFormatter(formatter)

app = FastAPI(title=" *** GRPC STUB [{{ service_name }}] *** ", version="1.0.1", redoc_url=None)

DTOs = _register_grpc_dto_(proto)
stubs: dict[str, Union[str, bytes]] = {}
requests: dict[str, str] = {}
REST_PORT: int = int(environ.get('REST_PORT'))
GRPC_PORT: int = int(environ.get('GRPC_PORT'))
NUM_WORKERS: int = int(environ.get('NUM_WORKERS'))


@app.get("/stubs")
async def watch_stubs():
    return stubs


@app.get("/requests")
async def watch_requests():
    return requests


@app.post("/define_stub")
async def create_stub(service: str, rpc: str, request: Request):
    body = await request.body()
    stubs[f'{service}::{rpc}'] = body
    return {"service": service, "rpc": rpc, "body": body}


def json_logs_converter(message):
    return dumps(MessageToDict(message=message,
                               including_default_value_fields=True,
                               preserving_proto_field_name=False),
                 ensure_ascii=False)


def fill_answer(marker: str, message, logger, base) -> object:
    if marker in stubs:
        requests[marker] = loads(MessageToJson(message, indent=2, ensure_ascii=False))
        return Parse(text=stubs[marker], message=base)
    logger.error('No defined stub!')
""".replace('{{ service_name }}', environ.get('PROTO_FILE').split('.')[0])\
    .replace('{{ protobuf_name }}', environ.get('PROTO_FILE'))


with open('server.py', "w", encoding='utf-8')as f:
    f.write(
        stub_file +
        grpc_service_template +
        grpc_run_server_template
    )

print(f'''
>>>>>> Server for {data['service_name']} is created >>>>>
>>>>>>>>>> And it ready to be launched >>>>>>>>>>>>>>
''')
