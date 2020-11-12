# WDRAX Plugins

This directory contains the set of default plugins which are available for the processing of Twitter extracts.

To enable a plugin, create a symlink to it, in the `plugins-enabled` directory.


## Available Plugins

### DOTWEETSTABLE

Ported from original WDRAX implementation.

Formats Tweet data as CSV for easier manual processing.

### DOTEXTTABLE

Not yet ported

### DOACCOUNTSTABLE

Not yet ported

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

The new implementation of WDRAX will pick up any files which a plugin outputs into the current working directory.

Previously, plugins output their data on stdout, now they should output it to a file.

Due to changes in the JSON format, each JQ file that begins with accessing user attributes first needs to index the user array, e.g.:

```
.[] |
.user.screen_name as $by |
...
```
