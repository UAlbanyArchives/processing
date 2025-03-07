import asnake.logging as logging
from asnake.client import ASnakeClient

logging.setup_logging(filename="/logs/aspace-flask.log", filemode="a", level="INFO")
client = ASnakeClient()

def add_aspace_items(refID, title_1, display_date_1, normal_date_1, title_2, display_date_2, normal_date_2):

    ref = client.get("repositories/2/find_by_id/archival_objects?ref_id[]=" + refID).json()
    item = client.get(ref["archival_objects"][0]["ref"]).json()

    if "/" in normal_date_1:
        new_date_1 = {
            'expression': display_date_1,
            'begin': normal_date_1.split("/")[0],
            'end': normal_date_1.split("/")[1],
            'date_type': 'inclusive',
            'label': 'creation',
            'jsonmodel_type': 'date'
        }
    else:
        new_date_1 = {
            'expression': display_date_1,
            'begin': normal_date_1,
            'date_type': 'single',
            'label': 'creation',
            'jsonmodel_type': 'date'
        }

    new_ao_1 = {
        'jsonmodel_type': 'archival_object',
        'publish': True,
        'external_ids': [],
        'subjects': [],
        'linked_events': [],
        'extents': [],
        'lang_materials': [],
        'dates': [new_date_1],
        'external_documents': [],
        'rights_statements': [],
        'linked_agents': [],
        'restrictions_apply': False,
        'ancestors': [],
        'instances': [],
        'notes': [],
        'level': 'item',
        'title': title_1,
        'resource': item['resource'],
        'parent': {"ref": item["uri"]}
    }

    if "/" in normal_date_2:
        new_date_2 = {
            'expression': display_date_2,
            'begin': normal_date_2.split("/")[0],
            'end': normal_date_2.split("/")[1],
            'date_type': 'inclusive',
            'label': 'creation',
            'jsonmodel_type': 'date'
        }
    else:
        new_date_2 = {
            'expression': display_date_2,
            'begin': normal_date_2,
            'date_type': 'single',
            'label': 'creation',
            'jsonmodel_type': 'date'
        }

    new_ao_2 = {
        'jsonmodel_type': 'archival_object',
        'publish': True,
        'external_ids': [],
        'subjects': [],
        'linked_events': [],
        'extents': [],
        'lang_materials': [],
        'dates': [new_date_2],
        'external_documents': [],
        'rights_statements': [],
        'linked_agents': [],
        'restrictions_apply': False,
        'ancestors': [],
        'instances': [],
        'notes': [],
        'level': 'item',
        'title': title_2,
        'resource': item['resource'],
        'parent': item
    }

    ao_1_res = client.post("repositories/2/archival_objects", json=new_ao_1)


    ao_2_res = client.post("repositories/2/archival_objects", json=new_ao_2)

    return ao_1_res, ao_2_res
