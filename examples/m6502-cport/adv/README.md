# Editable text adventure

`adventure.bas` is a small data-driven adventure engine. Rooms and objects
are stored in text files so the world can be changed without editing the
engine.

Run it from this directory so the relative data-file names resolve:

```powershell
cd cport\examples\adv
..\..\mbasic.exe adventure.bas
```

Commands and object names must be entered in uppercase. Supported commands
are `NORTH`, `SOUTH`, `EAST`, `WEST`, `GO direction`, `LOOK`,
`TAKE object`, `DROP object`, `EXAMINE object`, `INVENTORY`, `HELP`, and
`QUIT`.

## Room file

The first line of `rooms.txt` is the room count. Each following record is:

```text
name,description,north,south,east,west
```

Rooms are numbered by their order in the file, starting at 1. An exit value
of 0 means there is no exit in that direction. The engine starts in room 1
and supports up to 20 rooms.

## Object file

The first line of `objects.txt` is the object count. Each following record
is:

```text
name,description,starting-room,takeable
```

`takeable` is 1 for a portable object and 0 for scenery. A
`starting-room` of 0 places an object in the player's initial inventory.
The engine supports up to 30 objects.

Keep each field free of commas. Names should be uppercase because this
version of BASIC has no uppercase-conversion function.
