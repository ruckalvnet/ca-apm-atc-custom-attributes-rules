from optparse import OptionParser
import json
import logging
import sys
import requests
from pprint import pformat
import re
import urllib3
import copy
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def parser(args):
    """Script Arguments Parser ( using optparse module )"""

    opt_parser = OptionParser()

    opt_parser.add_option("-u", "--rest-url", dest="rest_url", help="CA APM Rest url")
    opt_parser.add_option("-t", "--api-token", dest="api_token", help="CA APM API Rest api token")
    opt_parser.add_option("-r", "--rules", dest="rules", help="Path to attributes rules file")
    opt_parser.add_option("-v", "--verbose_level", dest="verbose_level", default=20, help="Define log verbosity level")

    options = opt_parser.parse_args(args)[0]

    if not options.rest_url:
        opt_parser.error("CA APM Rest url is not defined! - (option -h for help)")
    if not options.api_token:
        opt_parser.error("CA APM API Rest api token is not defined! - (option -h for help)")
    if not options.rules:
        opt_parser.error("Path to attributes rules file is not defined! - (option -h for help)")

    return options


class ApmApi(object):
    """APM API Resource"""
    def __init__(self, rest_url, auth_token):
        self.rest_url = rest_url
        self.auth_token = auth_token
        self.headers = {
            'Content-type': 'application/hal+json;charset=utf-8',
            'Authorization': 'Bearer {}'.format(self.auth_token)
        }

    def get_vertex_list(self, lucene_query):
        """Get a vertex list base on lucene query"""
        response = requests.get('{0}/vertex?q={1}'.format(self.rest_url, lucene_query),
                                headers=self.headers, verify=False)
        vertex_list = response.json()['_embedded']['vertex']
        logging.debug(pformat(vertex_list))
        return vertex_list

    def update_vertex(self, vertex_id, attributes):
        """Update vertex_id object with specified attributes"""
        url = "{0}/graph/vertex/{1}".format(self.rest_url, vertex_id)
        payload = {}
        for key in attributes:
            payload[key] = [attributes[key]]

        update_payload = {'attributes': payload}
        logging.info("Updating vertex id {0} with attributes -> {1}".format(vertex_id, update_payload))
        response = requests.patch(url, json=update_payload, headers=self.headers, verify=False)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            logging.debug(response.text)
        return response


def init_logging(logging_level):
    """ Initialize logging facility
    Logging level - numeric value
    CRITICAL - 50 / ERROR - 40 / WARNING - 30 / INFO - 20 / DEBUG - 10 / NOTSET - 0 """
    logging.basicConfig(level=int(logging_level), format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    logging.info("Logging facility is loaded.")


def load_rules(json_file_path):
    """Load attributes rules file to dict"""
    with open(json_file_path) as f:
        data = json.load(f)
        logging.debug("Rules Loaded: {0}".format(pformat(data)))
        return data


def regex_replace_attributes(vertex_attrs, regex_expressions, new_attrs):
    """Replace new attributes values with variables if needed"""
    logging.debug("regex replace data: -> attributes: {0} \n-> regex expressions: {1} \n-> new attributes: {2}".format(
        pformat(vertex_attrs), pformat(regex_expressions), pformat(new_attrs)))
    format_groups = ()
    for rule in regex_expressions:
        r = re.compile(rule['expression'])
        attr = vertex_attrs[rule['attribute']]
        format_groups = format_groups + r.search(attr).groups()

    pattributes = {}
    for key, value in new_attrs.iteritems():
        if value is not None:
            pattributes[key] = value.format(*format_groups)
        else:
            pattributes[key] = None

    return pattributes


def vertex_needs_update(vertex_attrs, new_attrs):
    """remove attributes that already been set or deleted"""
    pattributes = copy.deepcopy(new_attrs)
    for key in new_attrs.keys():
        if (key in vertex_attrs and vertex_attrs[key] == new_attrs[key]) or \
                (key not in vertex_attrs and new_attrs[key] is None):
            del pattributes[key]

    return pattributes


def main():
    """Main logic."""
    args = parser(sys.argv)
    init_logging(args.verbose_level)
    data = load_rules(args.rules)
    apm_api = ApmApi(args.rest_url, args.api_token)
    count = 0
    for rule in data['rules']:
        logging.info("Executing rule with name: {0}".format(rule['name']))
        vertex_list = apm_api.get_vertex_list(rule['lucene_query'])
        for vertex in vertex_list:
            attr = rule['attributes']
            if 'regex' in rule:
                try:
                    attr = regex_replace_attributes(vertex['attributes'], rule['regex'], rule['attributes'])
                except KeyError as err:
                    logging.warn("Problem with key in this vertex: {0} \n-> rule: {1} \n-> KeyError: {2}".format(
                        pformat(vertex),
                        pformat(rule),
                        err))
                    continue
            fattrs = vertex_needs_update(vertex['attributes'], attr)
            if fattrs:
                apm_api.update_vertex(vertex['id'], fattrs)
                count += 1
            else:
                logging.debug("Vertex id {0} already updated with attributes: {1}".format(vertex['id'], attr))

    logging.info("Updated vertex count: {0}".format(count))


if __name__ == '__main__':
    main()
