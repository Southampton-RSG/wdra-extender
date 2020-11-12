# WDRAX Plugins

This directory contains the set of default plugins which are available for the processing of Twitter extracts.

To enable a plugin, create a symlink to it, in the `plugins-enabled` directory.


## Available Plugins

### DOTWEETSTABLE

Ported from original WDRAX implementation.

Formats Tweet data as CSV for easier manual processing.

### DOTEXTTABLE

Ported from original WDRAX implementation.

Collects hashtags and their frequencies.

### DOACCOUNTSTABLE

Ported from original WDRAX implementation.

Renders user accounts and relationships to a D3 chart.

### DOMISC

Not yet ported.
Is not used in original WDRAX implementation.

### DOWORDCLOUD

Not yet ported.

### DOKWIK

Not yet ported.

### DOIMG

Not yet ported.


## Porting a Plugin

A plugin is a directory containing a `main.*` (e.g. `main.sh`, `main.py`) executable file.
This executable file receives a path to the Twitter JSON data as its first argument and is expected to write a number of output files into the current working directory.
These output files are collected and zipped to be returned to the user.

Changes compared to the original implementation:
- Each plugin goes in its own subdirectory
  - The subdirectory is the plugin name
- Each plugin must be named `main.*`
- Output should be written to files in the current working directory
  - Used to be to stdout
- Twitter API credentials are available as environment variables
  - Don't need a Twarc config file anymore

Due to changes in the JSON format, each JQ file that begins with accessing user attributes first needs to index the user array, e.g.:

```
.[] |
.user.screen_name as $by |
...
```
