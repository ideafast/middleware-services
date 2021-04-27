Compare contribution differences, or get an overview of upload coverage for each patient using the commands below. Make sure you have the appropriate `dmp_tools` environmental variables set.

## Diff tool
To Compare the upload of WP3 Pipeline to all other users to debug and test it's behaviour run:

```shell
python data_transfer/dmp_tools/contribution_diff.py [devicetype] [studysite]
python data_transfer/dmp_tools/contribution_diff.py BTF Kiel  (for example)
```
This outputs the diffs in the terminal as well as root/dmp_tools_output/


