
# Jellyfin metadata editor

This app allows easy updating of metadata for collections or series where metadata isn't available or accurate.

## Usage/Examples


- You want to add Tags / Genres
- You want to format titles
![Example of adding tags and formatting name](/images/use_example_1.gif)


## Supported Fields

| Field             | Info                                                                | Safe to Change? |
| ----------------- | ------------------------------------------------------------------ | ------ |
| Name | This is the main title displayed in Jellyfin | Yes |
| Overview | This is essentially a synopsis | Untested... but probably okay|
| Tags | Tags in Jellyfin | Yes |
| Genres | Genres in Jellyfin | Yes |
| Studios | Studios in Jellyfin |  Untested... but probably okay |
| ProductionLocations | Locations in Jellyfin | Untested... but probably okay |
| PremiereDate | The releasedate in Jellyfin | Untested... change with caution |
| EpisodeTitle | I don't know what this does | Untested... but probably okay |


## Built-in Tools

### Entry Tools
- Remove special characters and numbers. (Clean Text checkbox)
- Remove dates following 1999.1.1 format. (Remove Dates checkbox)

### Separated Value Tools
This is for fields that are separated with "|" inside the Jellyfin library.db

- Add common values to your config.
- Easily toggle to remove/add a value.
- Auto add values if the value is present in the Name of the episode. (Auto Add checkbox)

### TODO

- Date Tools
- Auto Update All
## How To Use

### Prepare your Jellyfin
Your collection has to be saved in Jellyfin as a series, in order for this app to locate it. 

So your Jellyfin Media Library should have a content type = Shows and your collection should be in a parent directory for a common name.

### Example
<details>
<summary>My Setup For Howard Stern</summary>
My folder structure is media/Howard Stern/Howard.Stern.On.Demand/ All my files

Then this is is my Jellyfin Media Library

![jelly structure](/images/example_jellyfin.png)
</details>

### Select A Series And Start Editing