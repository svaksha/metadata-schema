# from schema_test_suite import get_json_from_file
import logging
import os
import re
import json


allowed_root_level_keywords = ['$schema', 'description', 'additionalProperties', 'required', 'title', 'name', 'type', 'properties', 'definitions']

required_root_level_keywords = ['$schema', 'description', 'additionalProperties', 'title', 'name', 'type', 'properties']

essential_properties = ['describedBy', 'schema_version']
# , 'schema_type', 'provenance']

property_keywords = ['description', 'type', 'pattern', 'example', 'enum', '$ref', 'user_friendly', 'items', 'guidelines', 'format', 'comment', 'maximum', 'minimum']

ontology_keywords = ['graph_restriction', 'ontologies', 'classes', 'relations', 'direct', 'include_self']

system_supplied_properties = ['describedBy', 'schema_version', 'schema_type', 'provenance']


class SchemaLinter:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def lintSchema(self, path):
        schema = self.get_json_from_file(path)
        properties = schema['properties']

        # SCHEMA-LEVEL CHECKS

        schema_filename = path.split("/")[-1].split(".")[0]

        # Check that all root level fields in the schema are part of the list of allowed root level fields
        for key in schema.keys():
            if key not in allowed_root_level_keywords:
                print("Root level field `" + key + "` in schema " + path + " not part of allowed root level properties")

        # Check that all required root level fields are present in the schema
        for prop in required_root_level_keywords:
            if prop not in schema.keys():
                print(schema_filename + ".json: Missing required root level field `" + prop + "`")

        # Check that additionalProperties is set to false
        if "additionalProperties" in schema and schema['additionalProperties'] == True:
            print(schema_filename + ".json: Should not allow additional properties")

        # Check that $schema is set to draft-07
        if "$schema" in schema and schema['$schema'] != "http://json-schema.org/draft-07/schema#":
            print(schema_filename + ".json: Must have $schema set to http://json-schema.org/draft-07/schema#")

        # Check that the name of the schema in the describedBy URL is set to the schema filename
        if properties['describedBy']['pattern'].split("/")[-1] != schema_filename:
            print(schema_filename + ".json: End of `describedBy` URL (" + properties['describedBy']['pattern'].split("/")[-1] + ") must match schema filename (" + schema_filename + ")")

        # Check that the schema name attribute is set to the schema filename
        if "name" in schema and schema['name'] != schema_filename:
            print(schema_filename + ".json: The `name` attribute (" + schema['name'] + ") must match the schema filename (" + schema_filename + ")")

        # Check that schema type is set to object
        if "type" in schema and schema['type'] != "object":
            print(schema_filename + ".json: The `type` attribute must be set to object")

        # Check that all required fields are actually in the schema
        if "required" in schema:
            for req_prop in schema["required"]:
                if req_prop not in properties:
                    print("Property `" + req_prop + "` is required in " + schema_filename + ".json but is undefined")

        # PROPERTY-LEVEL CHECKS

        # Check that essential properties `describedBy` and `schema_version` are present
        for ep in essential_properties:
            if ep not in properties:
                print(schema_filename + ".json: Missing required property `" + ep + "`")

        for property in properties:
            # print(property)
            # Check that property name contains only lowercase letters, numbers, and underscores
            if not re.match("^[a-z0-9_]+$", property) and property not in ['describedBy']:
                print(schema_filename + ".json: Property `" + property + "` contains non-lowercase/underscore characters")

            # Check that property contains description attribute
            if 'description' not in properties[property].keys():
                print(schema_filename + ".json: Keyword `description` missing from property `" + property + "`")

            # Check that description attribute is a sentence - start with capital letter and end with full stop
            if 'description' in properties[property].keys() and not re.match('^[A-Z][^?!]*[.]$', properties[property]['description']):
                print(schema_filename + ".json: The `description` for property `" + property + "` is not a sentence (" + properties[property]['description'] + ")")

            # Check that property contains user-friendly attribute
            # Currently excludes ingest-supplied fields
            # Currently excludes links.json and provenance.json
            if property not in ['provenance', 'schema_version', 'schema_type', 'describedBy'] and 'user_friendly' not in properties[property].keys():
                if schema_filename not in ["links", "provenance"]:
                    print(schema_filename + ".json: Keyword `user_friendly` missing from property `" + property + "`")

            # Check that if property contains format attribute, format is valid JSON format
            if 'format' in properties[property].keys() and properties[property]['format'] not in ["date", "date-time", "email"]:
                print(schema_filename + ".json: Format `" + properties[property]['format'] + "` is not a valid JSON format)")

            # Check that guidelines attribute is a sentence
            if 'guidelines' in properties[property].keys() and not re.match('^[A-Z][^?!]*[.]$', properties[property]['guidelines']):
                print(schema_filename + ".json: The `guidelines` for property `" + property + "` is not a sentence (" + properties[property]['guidelines'] + ")")

            # Check that property contains type attribute
            if 'type' not in properties[property].keys():
                print(schema_filename + ".json: Keyword `type` missing from property `" + property + "`")

            else:
                # Check that 'type' attribute is set to one of the valid JSON types
                if properties[property]['type'] not in ["string", "number", "boolean", "array", "object", "integer"]:
                    print(schema_filename + ".json: Type `" + properties[property]['type'] + "` is not a valid JSON type")

                # Check that property of type array also contains the attribute items
                if properties[property]['type'] == "array" and 'items' not in properties[property].keys():
                    print(schema_filename + ".json: Property `" + property + "` is type array but doesn't contain items")

                # Check that a property of type array contains the attribute items and items has either the type or $ref attribute
                if properties[property]['type'] == "array" and 'items' in properties[property].keys() and '$ref' not in properties[property]['items'].keys() and 'type' not in properties[property]['items'].keys():
                    print(schema_filename + ".json: Property `" + property + "` is type array but items attribute doesn't contain type or $ref attribute")

                # Check that property of type object also contains the attribute $ref
                if properties[property]['type'] == "object" and '$ref' not in properties[property].keys():
                    print(schema_filename + ".json: Property `" + property + "` is type object but doesn't contain $ref")

            # Check that property contains example attribute
            # Except for system-supplied fields
            # Except when importing module ($ref)
            if 'example' not in properties[property].keys() and property not in system_supplied_properties and schema_filename not in ['links', 'provenance']:
                if 'items' in properties[property].keys() and '$ref' not in properties[property]['items'].keys():
                    print(schema_filename + ".json: Keyword `example` missing from property `" + property + "`")
                elif 'items' not in properties[property].keys() and '$ref' not in properties[property].keys():
                    print(schema_filename + ".json: Keyword `example` missing from property `" + property + "`")
            # Check that there are 1 or 2 examples separated by semicolon
            # Excludes enums that list all valid values (Should be one of)
            elif 'example' in properties[property].keys() and property not in system_supplied_properties and schema_filename not in ['links', 'provenance']:
                if not re.match("^Should be one of", str(properties[property]['example'])):
                    ex = str(properties[property]['example']).split(";")
                    if len(ex) == 1 and re.search(",", ex[0]):
                        print(schema_filename + ".json: Property `" + property + "` might have multiple examples that aren't separated by a semicolon (" + str(properties[property]['example']) + ")")

            # Check that _unit properties having matching property w/o unit
            if re.match("^[a-z_]+_unit$", property):
                if property.split("_unit")[0] not in properties:
                    print(schema_filename + ".json: Has unit property `" + property + "` but no corresponding `" + property.split("_unit")[0] + "` property")

            for kw in properties[property].keys():
                if property == 'ontology' and kw == 'graph_restriction':
                    nested_keywords = properties[property][kw]
                    for nkw in nested_keywords.keys():
                        if nkw not in ontology_keywords:
                            print("Keyword `" + nkw + "` is not in the list of acceptable ontology keyword properties")
                elif kw not in property_keywords:
                    print("Keyword `" + kw + "` in property `" + property + "` is not in the list of acceptable keyword properties")

                if isinstance(properties[property][kw], dict) and property != 'ontology':
                    for nkw in properties[property][kw].keys():
                        if nkw not in property_keywords:
                            print("Keyword `" + nkw + "` in property `" + property + "` is not in the list of acceptable keyword properties")


    def get_json_from_file(self, filename, warn = False):
        """Loads json from a file.
        Optionally specify warn = True to warn, rather than
        fail if file not found."""
        f = open(filename, 'r')
        return json.loads(f.read())


if __name__ == '__main__':
    schema_path = '../json_schema'

    linter = SchemaLinter()

    jsons = [os.path.join(dirpath, f)
               for dirpath, dirnames, files in os.walk(schema_path)
               for f in files if f.endswith('.json')]

    # Exclude top-level JSON files like versions.json and property_migrations.json
    # by including JSON file only if the path contains "core", "module", "system", or "type"
    schemas = [j for j in jsons if any(substring in j for substring in ("core", "module", "system", "type"))]

    print("Checking %d schemas" % len(schemas))

    for s in schemas:
        if 'versions.json' not in s:
            # print('Checking %s' % s)
            linter.lintSchema(s)
