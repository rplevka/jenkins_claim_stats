# Manipulate Jenkins claims with grace

For example to config, see `config.yaml.sample`.

For example on how knowleadge base could look like see `kb.json.sample`.

```
$ ./claims-cmd.py --help
usage: claims-cmd.py [-h] [--clean-cache] [--show-failed] [--show-claimed]
                     [--show-unclaimed] [--show-claimable] [--show SHOW]
                     [--claim] [--stats] [--history] [--timegraph]
                     [--job-group JOB_GROUP] [--grep-results REGEXP]
                     [--grep-rules REGEXP] [--output {simple,csv,html}] [-d]

Manipulate Jenkins claims with grace

optional arguments:
  -h, --help            show this help message and exit
  --clean-cache         Cleans cache for job group provided by "--job-group"
                        option (default: latest)
  --show-failed         Show all failed tests
  --show-claimed        Show claimed tests
  --show-unclaimed      Show failed and not yet claimed tests
  --show-claimable      Show failed, not yet claimed but claimable tests
  --show SHOW           Show detailed info about given test case
  --claim               Claim claimable tests
  --stats               Show stats for selected job group
  --history             Show how tests results and duration evolved
  --timegraph           Generate time graph
  --job-group JOB_GROUP
                        Specify group of jobs to perform the action with
                        (default: latest)
  --grep-results REGEXP
                        Only work with tests, whose "className+name" matches
                        the regexp
  --grep-rules REGEXP   Only work with rules, whose reason matches the regexp
  --output {simple,csv,html}
                        Format tables as plain, csv or html (default: simple)
  -d, --debug           Show also debug messages
```
