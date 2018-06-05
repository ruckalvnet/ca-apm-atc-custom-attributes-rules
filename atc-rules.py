from optparse import OptionParser
import json
import logging
import sys
import requests
from pprint import pformat
import re
import urllib3
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


def parse_regex_attribute(text, regex, attributes):
    """Replace attributes values with variables if needed"""
    logging.debug("{0} -> {1} -> {2}".format(text, regex, attributes))
    r = re.compile(regex)
    pattributes = {}
    for key, value in attributes.iteritems():
        if value:
            pattributes[key] = value.format(*r.search(text).groups())
    return pattributes


def main():
    """Main logic."""
    args = parser(sys.argv)
    init_logging(args.verbose_level)
    data = load_rules(args.rules)
    apm_api = ApmApi(args.rest_url, args.api_token)
    for rule in data['rules']:
        logging.info("Executing rule with name: {0}".format(rule['name']))
        vertex_list = apm_api.get_vertex_list(rule['lucene_query'])
        for vertex in vertex_list:
            attr = rule['attributes']
            if 'regex' in rule:
                attr = parse_regex_attribute(vertex['attributes'][rule['regex']['attribute']],
                                             rule['regex']['expression'],
                                             attr)
            apm_api.update_vertex(vertex['id'], attr)


if __name__ == '__main__':
    main()
