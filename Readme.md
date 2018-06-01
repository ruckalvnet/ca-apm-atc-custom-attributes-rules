# CA APM ATC custom attributes 

This python script can be used to populate APM TeamCenter with custom attributes from a json file. 
The rules in json file will be applied sequentially.

### Prerequisites
First we need to clone the project from github:
```
git clone <repository url> 
```
The script was tested with python version 2.7. 
Run the following pip command to install the needed "requests" module
 if it's missing from your python installation:
```
pip install -r requirements.txt
```

### Installing

Script usage:
```
Usage: atc-rules.py [options]

Options:
  -h, --help                                        show this help message and exit
  -u REST_URL, --rest-url=REST_URL                  CA APM Rest url
  -t API_TOKEN, --api-token=API_TOKEN               CA APM API Rest api token
  -r RULES, --rules=RULES                           Path to attributes rules file
  -v VERBOSE_LEVEL, --verbose_level=VERBOSE_LEVEL   Define log verbosity level
```
Example command line:
```
python atc-rules.py -u http://localhost:8080/apm/appmap -t 5df89644-00d0-4dd6-937f-e1b9a5c11dec -r rules.json
```

JSON Rules file explained (rules.json):

```
{
  "rules": [              <- Json Array for rules. Rules are executed sequentially.>
    {
      "name":"<mandatory - just a description and identifier for the rule. Not used by application>",
      "lucene_query": "<mandatory - filtering vertex list with Lucene syntax (https://lucene.apache.org/core/4_7_0/queryparser/org/apache/lucene/queryparser/classic/package-summary.html)>",
      "regex":{           <- optional - if needed capture substring from vertex attribute with regex expression >
        "attribute":"agent",
        "expression":"(.*)-agent-(.*)$"
      },
      "attributes": {                           <- mandatory - define attributes to be updated with this rule. >
        "applicationServer": "jvm-{0}",         <- you can replace variable {0} with the first match in regex >
        "applicationPlatform": "platform-{1}"   <- you can replace variable {1} with the second match in regex >
      }                                         <  if the attribute value is set to null (without quotes), the                     
    },                                              attributed is deleted from ATC >            
    {
      "name":"second rule as an example",
      "lucene_query":"(attributes.agentDomain:SuperDomain/testDomain AND attributes.agent:/.*test.*/)",
      "attributes": {
        "exampleAttribute": "exampleValue"
      }
    }
  ]
}
```

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the tags on this repository 

## Authors

* **Rui Alves** - *Initial work*

## License

This project is licensed under the MIT License - see the [LICENSE](LICENCE) file for details

