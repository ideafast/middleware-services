Compare contribution differences, or get an overview of upload coverage for each patient using the commands below. Make sure you have the appropriate `dmp_tools` environmental variables set.

## Diff tool
To Compare the upload of WP3 Pipeline to all other users to debug and test it's behaviour run:

```shell
python data_transfer/dmp_tools/contribution_diff.py [devicetype] [studysite]
python data_transfer/dmp_tools/contribution_diff.py BTF Kiel  (for example)
```
This outputs the diffs in the terminal as well in root/dmp_tools_output/

## Diff tool
To get an overview of data on the DMP per-patient for a studysite, run

```shell
python data_transfer/dmp_tools/site_overview.py [studysite]
python data_transfer/dmp_tools/contribution_diff.py Kiel  (for example)
```
This outputs the overiew in .json in the terminal and a .json and .csv as well in root/dmp_tools_output/

> Note that this overview ignores 'gaps' in data, and aggregates periods of data by their min and max values.

