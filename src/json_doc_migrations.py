from argparse import ArgumentParser
import json
from collections import defaultdict
from itertools import chain


class Migrator:

    def add_property(self, json_doc, migration):
        new_prop = migration["replaced_by"].split(".")




    def remove_property(self, json_doc, migration):
        print("foo")

    def rename_property(self, json_doc, migration):
        print("foo")

    def move_property_in_schema(self, json_doc, migration):
        source_prop = migration["property"].split(".")
        new_prop = migration["replaced_by"]

        value = json_doc
        for key in source_prop[1:]:
            value = value[key]
        for part in reversed(new_prop.split('.')[1:]):
            value = {part: value}

        json_doc = self._mergeDict(json_doc, value)

        json_doc = self._removeSourceProp(json_doc, source_prop)


        return self._update_schema_version(json_doc, migration)

    def move_property_across_schemas(self, json_doc, target_doc, migration):
        print("foo")

    def _update_schema_version(self, json_doc, migration):
        schema_uri = json_doc["describedBy"]
        current_version = json_doc["schema_version"]
        new_version = migration["effective_from"]

        new_uri = schema_uri.replace(current_version, new_version)

        json_doc["describedBy"] = new_uri
        json_doc["schema_version"] = new_version
        return  json_doc

    def _mergeDict(self, dict1, dict2):
        dict3 = defaultdict(list)
        for k, v in chain(dict1.items(), dict2.items()):
            if k in dict3:
                if isinstance(v, dict):
                    dict3[k].update(self._mergeDict(dict3[k], v))
                elif isinstance(v, list) and isinstance(dict3[k], list) and len(v) == len(dict3[k]):
                    for index, e in enumerate(v):
                        dict3[k][index].update(self._mergeDict(dict3[k][index], e))
                else:
                    dict3[k].update(v)
            else:
                dict3[k] = v
        return dict3

    def _removeSourceProp(self, json_dict, prop):
        new_dict = defaultdict(list)
        for k,v in chain(json_dict.items()):
            if k not in prop or (k in prop and not isinstance(v, dict)):
                if isinstance(v, dict):
                    for d in self._removeSourceProp(v, prop):
                        new_dict[k] = d
                elif isinstance(v, list):
                    for index, e in enumerate(v):
                        new_dict[k][index] = e
                else:
                    new_dict[k] = v
            else:
                print("Not adding " + k + " " + v)
        return new_dict



def _open_file(filename):
    f = open(filename, 'r')
    return json.loads(f.read())

def _save_json(path, data):
    with open(path, 'w') as outfile:
        json.dump(data, outfile, indent=4, sort_keys=True)




if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-f", "--f", dest="files", action="append",
                      help="JSON document to migrate")
    parser.add_argument("-m", "--m", dest="migration",
                      help="Migration document")

    args = parser.parse_args()

    docs = []

    if args.files:
        for file in args.files:
            docs.append(_open_file(file))
    else:
        print("You have to provide a JSON document to migrate")
        exit(2)

    if args.migration:
        migration = _open_file(args.migration)
    else:
        print("You have to provide a migration strategy document")
        exit(2)

    counter = 0
    for m in migration["migrations"]:

        #     check the first part of property or replaced_by against the doc's describedBy link
        if "property" not in m:
            for doc in docs:
                if m["replaced_by"].split(".")[0] in doc["describedBy"]:
                    new_doc = Migrator().add_property(doc, m)
                    _save_json("updated_file_" + str(counter) + ".json", new_doc)
                    counter += 1
        if "replaced_by" not in m:
                for doc in docs:
                    if m["property"].split(".")[0] in doc["describedBy"]:
                        new_doc = Migrator().remove_property(doc, m)
                        _save_json("updated_file_" + str(counter) + ".json", new_doc)
                        counter += 1

        if m["property"].split(".")[0] == m["replaced_by"].split(".")[0]:
                for doc in docs:
                    if m["property"].split(".")[0] in doc["describedBy"]:
                        new_doc = Migrator().move_property_in_schema(doc, m)
                        _save_json("updated_file_" + str(counter) + ".json", new_doc)
                        counter += 1

        if m["property"].split(".")[0] != m["replaced_by"].split(".")[0]:
            for doc in docs:
                if m["property"].split(".")[0] in doc["describedBy"]:
                    source_doc = doc
                elif m["replaced_by"].split(".")[0] in doc["describedBy"]:
                    target_doc = doc
            new_docs = Migrator().move_property_across_schemas(source_doc, target_doc, m)
            for nd in new_docs:
                _save_json("updated_file_" + str(counter) + ".json", nd)
                counter += 1



