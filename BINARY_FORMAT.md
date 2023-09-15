# Zoom Project Binary File Format

Typically stored in `PRJDATA.ZDT`

## Header Section: 0x0000-005F (96 bytes)

### Bytes: 0x0000-001E (31 bytes)

Seems to be the string `ZOOM R-16  PROJECT DATA VER0001`.

### Bytes: 0x001E-001F (1 byte)

Space

### Bytes: 0x0020-002E (15 bytes)

Spaces

### Bytes: 0x002F-0033 (5 bytes)

NULLs

### Bytes: 0x0034-003B (8 bytes)

Project Name

### Bytes: 0x003C-0053 (28 bytes)

NULLs

### Bytes: 0x0054-0057 (4 bytes)

`FF FF 00 00` Magic Number?

### Bytes: 0x0058-005F (8 bytes)

F&F Hex: `18 00 00 00 00 00 00 00`

This seems to be related to INSERT EFFECT.

When I turned it on for a project, the byte at 0x0058 changed from `0` to `08`. Maybe this is simply an On/Off bit that is set.

UPDATE: When I changed from `TR1` as INPUT SOURCE to `IN5`, this value changed from `08` to `04`.

Current values:

| Hex Value:    | 0    | 4     | 8     | 0x18     |
| ------------- | ---- | ----- | ----- | -------- |
| INPUT SOURCE: | N/A? | `IN5` | `TR1` | `MASTER` |

Possible full range of values

| Hex Value:    | 0     | 1     | 2     | 3     | 4     | 5     | 6     | 7     |
| ------------- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- |
| INPUT SOURCE: | `IN1` | `IN2` | `IN3` | `IN4` | `IN5` | `IN6` | `IN7` | `IN8` |

| Hex Value:    | 8     | 9     | A     | B     | C     | D     | E     | F     |
| ------------- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- |
| INPUT SOURCE: | `TR1` | `TR2` | `TR3` | `TR4` | `TR5` | `TR6` | `TR7` | `TR8` |

| Hex Value:    | 10    | 11     | 12     | 13     | 14     | 15     | 16     | 17     |
| ------------- | ----- | ------ | ------ | ------ | ------ | ------ | ------ | ------ |
| INPUT SOURCE: | `TR9` | `TR10` | `TR11` | `TR12` | `TR13` | `TR14` | `TR15` | `TR16` |

| Hex Value:    | 18       |
| ------------- | -------- |
| INPUT SOURCE: | `MASTER` |

Questions:
* How to specify Track1 OR Track 2 (for mono tracks on DUAL effect)?
* How to specify Track1 AND Track 2 (for stereo tracks)
* How to specify Track 1-8 (or Track 9-16) for `8xCompEQ` effects?

## Fader Section: 0x0060-009F (64 bytes)

Each 4 byte value is the numeric representation of the FADER, starting at Track #1, going to Track #16.

Each value is equivalent to the decimal value shown in the UI.

Default value seems to be 100 (0x64).

## Pan Section: 0x00A0-00DF (64 bytes)

Each 4 byte value is the numeric representation of the PAN, starting at Track #1, going to Track #16.

A value of 50 (0x32) is equivalent to "C".
A value of 0 (0x00) is equivalent to "L100".
A value of 44 (0x2C) is equivalent to "L12".
A value of 56 (0x38) is equivalent to "R12".

To compute value: PAN === 'C' ? 50 : (PAN LEFT ? 50 - (pV/2) : 50 + (pV/2))

Default value seems to be 50 (0x32).

## Chorus Send Section: 00E0-011F (64 bytes)

Each 4 byte value is the numeric representation of the CHORUS SEND value, starting at Track #1, going to Track #16.

The value does _NOT_ indicate whether the CHORUS SEND is On or Off, but just the numeric value, if it was turned on. That is stored at 0x05BC.

## Reverb Send Section: 0x120-015F (64 bytes)

Each 4 byte value is the numeric representation of the REVERB SEND value, starting at Track #1, going to Track #16.

The value does _NOT_ indicate whether the REVERB SEND is On or Off, but just the numeric value, if it was turned on. That is stored at 0x05C0.

## Unknown Section ("UNKNOWN1"): 0x0160-019F (64 bytes)

For this project, all of the values are 0. This seems to be the INVERT setting, organized a single byte values from Track 1 to 16?

## EQ Section: 0x01A0-049F (768 bytes)

This seems to be 16 sets of 48 bytes. Each 48 byte section consists of 12 4-byte values:

Hex: `1 0xC 0 0xC 1 0xE 4 0xC 1 5 0 0xC`
Dec: `1 12 0 12 1 14 4 12 1 5 0 12`

These seem to be default values with the following possible assignments:

1. EQ Hi On/Off (1: On, is default)
1. EQ Hi Freq (0xC: 8kHz, is default)
1. ??? Maybe EQ Hi Q-Factor (which doesn't exist in UI)
1. EQ Hi Gain (0xC: 0dB, is default)
1. EQ Mid On/Off (1: On, is default)
1. EQ Mid Freq (0xE, 1kHz, is default)
1. EQ Mid Q-Factor (4, 0.5, is default)
1. EQ Mid Gain (0xC: 0dB, is default)
1. EQ Lo On/Off (1: On, is default)
1. EQ Lo Freq (5, 125Hz, is default )
1. ??? Maybe EQ Lo Q-Factor (which doesn't exist in UI)
1. EQ Lo Gain (0xC: 0dB, is default)

### EQ Gain

| Gain Values: | -12 | -11 | -10 | -9  | -8  | -7  | -6  | -5  | -4  | -3  | -2  | -1  | 0   |
| ------------ | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Hex Values:  | 0   | 1   | 2   | 3   | 4   | 5   | 6   | 7   | 8   | 9   | A   | B   | C   |

| Gain Values: | 1   | 2   | 3   | 4   | 5   | 6   | 7   | 8   | 9   | 10  | 11  | 12  |
| ------------ | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Hex Values:  | D   | E   | F   | 10  | 11  | 12  | 13  | 14  | 15  | 16  | 17  | 18  |

### EQ Hi Freq

| EQ&nbsp;Hi&nbsp;Freq&nbsp;Settings: | 500 | 630 | 800 | 1.0k | 1.3k | 1.6k | 2.0k | 2.5k | 3.2k | 4k  | 5k  |
| ----------------------------------- | --- | --- | --- | ---- | ---- | ---- | ---- | ---- | ---- | --- | --- |
| Hex Values:                         | 0   | 1   | 2   | 3    | 4    | 5    | 6    | 7    | 8    | 9   | A   |

| EQ Hi Freq Settings: | 6.3k | 8k (def) | 10k | 12.5k | 16k | 18k |
| -------------------- | ---- | -------- | --- | ----- | --- | --- |
| Hex Values:          | B    | C        | D   | E     | F   | 10  |

### EQ Mid Freq

| EQ Mid Freq Settings: | 40  | 50  | 63  | 80  | 100 | 125 | 160 | 200 | 250 | 315 | 400 |
| --------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Hex Values:           | 0   | 1   | 2   | 3   | 4   | 5   | 6   | 7   | 8   | 9   | A   |

| EQ&nbsp;Mid&nbsp;Freq&nbsp;Settings: | 500 | 630 | 800 | 1.0k (def) | 1.3k | 1.6k | 2.0k | 2.5k | 3.2k | 4k  |
| ------------------------------------ | --- | --- | --- | ---------- | ---- | ---- | ---- | ---- | ---- | --- |
| Hex Values:                          | B   | C   | D   | E          | F    | 10   | 11   | 12   | 13   | 14  |

| EQ Mid Freq Settings: | 5k  | 6.3k | 8k  | 10k | 12.5k | 16k | 18k |
| --------------------- | --- | ---- | --- | --- | ----- | --- | --- |
| Hex Values:           | 15  | 16   | 17  | 18  | 19    | 1A  | 1B  |

### EQ Q Factor (only for EQ Mid)

| EQ Mid Q Factor Settings: | 0.1 | 0.2 | 0.3 | 0.4 | 0.5 (def) | 0.6 | 0.7 | 0.8 | 0.9 | 1.0 |
| ------------------------- | --- | --- | --- | --- | --------- | --- | --- | --- | --- | --- |
| Hex Values:               | 0   | 1   | 2   | 3   | 4         | 5   | 6   | 7   | 8   | 9   |

### EQ Lo Freq

| EQ&nbsp;Lo&nbsp;Freq&nbsp;Settings: | 40  | 50  | 63  | 80  | 100 | 125 (def) | 160 | 200 | 250 | 315 | 400 |
| ----------------------------------- | --- | --- | --- | --- | --- | --------- | --- | --- | --- | --- | --- |
| Hex Values:                         | 0   | 1   | 2   | 3   | 4   | 5         | 6   | 7   | 8   | 9   | A   |

| EQ Lo Freq Settings: | 500 | 630 | 800 | 1.0k | 1.3k | 1.6k |
| -------------------- | --- | --- | --- | ---- | ---- | ---- |
| Hex Values:          | B   | C   | D   | E    | F    | 10   |

## Unknown Section ("UNKNOWN2"): 0x04A0-0x04A7 (8 bytes)

Seems to be related to INSERT EFFECT. There are two parts to the effect: ALGORITHM and PATCH (number and name). Though it appears that the PATCH number (and name) seems to be stored in the `EFXDATA.ZDT` file. This leaves only ALGORITHM.

For the `BlankCopyPlusTrackWithInsertEffect.zdt`, I selected the ALGORITHM to be `MIC` (and the PATCH to be `1`, `RoomAmbi`).

The default value of address 0x04A5 seems to be 0x64 (100). For other projects, this is different:

-   It is `0x43` (67) for `BlankCopyPlusTrackWithInsertEffect`. Maybe this is `MIC`?
-   It is `0x35` (53) for `FieldsAndForests`. Maybe this is `MASTERING`?

## Track Names Section: 0x04A8-0x05B7 (272 bytes)

There are 17 sets of 16 bytes of file names. Though the file names are restricted to being 12 chars (8 for the name, 1 for "." and 3 for the suffix), the extra bytes are NULLs. They are ordered from Track 1-16, followed by the name of the MASTERING file.

## Unknown Section: 0x05B8-0x05BB (4 bytes)

NULLs

## Chorus Send On/Off Section: 0x05BC-0x05BF (4 bytes)

Seems that the default is `FF FF 00 00` for these four bytes (with the first 16 bits indicating that Chorus Send is ON, by default for all Tracks).

The first byte is for Tracks 8 down to 1. The second byte is for Tracks 16 down to 9.

## Reverb Send On/Off Section: 0x05C0-09C3 (4 bytes)

Seems that the default is `FF FF 00 00`, similar to Chorus Send.

For F&F, `E1 C4` is a 16-bit value where the following bits are SET: 15, 14, 13, 8, 7, 6, and 2.

It seems like the way to interpret it is `E1` is the settings for Tracks 8 down to 1. This has bits set for Tracks 1, 6, 7, and 8. `C4` is the settings for Tracks 16 down to 9. This has bits set for Tracks 11, 15 and 16.

## Unknown Section: 0x05C4-09AB (1000 bytes)

NULLs

## Unknown Section: 0x09AC-0x09AF (4 bytes)

F&F Hex: `98 3A 00 00`
WinterSpells Hex: `93 81 00 00`

## Unknown Section: 0x09B0-0x0A23 (116 bytes? Or 120?)

Most of the values seem like 64 bit, negative values. What is ODD is that there are 15, 8 byte values, instead of 16.

## Unknown Section: 0x0A24-0CC3 (672 bytes)

NULLs

# Unknown Section: 0x0CC4-0D03 (64 bytes)

Hex: `0x0000000F (7 4-byte NULLs) 0x0050000 0x00000000 0x00000004 0x00000029 0x00000000 0x00000032 0x00000000`

# Addendum

## Track Info

Each track has the following fields with possible representations:

-   Pan: L100-C-R100. 201 distinct values. 8 bits.
-   EQ Hi Gain: -12 - +12. 25 distinct values. 5 bits.
-   EQ Hi Freq: 500-18k. Maybe 12 values? 4 bits.
-   EQ Mid Gain: 5 bits
-   EQ Mid Freq: 4 bits?
-   EQ Mid Q Factor: 0.1-1.0. 10 values. 3 bits.
-   EQ Lo Gain: 5 bits.
-   EQ Lo Freq: 3 bits?
-   Reverb Send: 0-100. 7 bits.
-   Chorus Send: 0-100. 7 bits.
-   Stereo Link: On, Off. 1 bit.
-   Invert: On, off. 1 bit.

Total: 53 bits. 7 bytes, minimum.

### F&F Track #1

Looking for Reverb Send (Track #1): 35, 0x23
Looking for Fader (Track #1): 124, 0x7C

### F&F Track #2

Looking for Pan (Track #2): L12, could be +12 (0x0C)
Looking for EQ Hi Gain (Track #2): 7 (0x07)
Looking for EQ Hi Freq (Track #2): 5kHz (could be any enum value)
Looking for Fader (Track #2): 119 (0x77)

### F&F Track #3

Looking for Pan (Track #3): R12, could be -12 (0xF3, ones comp), (0xF8, twos comp) or it could be 112 (0x70) (where L100=0, C=100, R1=101, R100=120)
Looking for EQ Hi Gain (Track #3): 7 (0x07)
Looking for EQ Hi Freq (Track #3): 5kHz (could be any enum value)
Looking for Fader (Track #3): 126 (0x7E)

### F&F Track #4

Looking for Pan (Track #4): L30, could be -30 (0xE1, ones comp), (0xE2, twos comp) or it could be 70 (0x46) (where L100=0, L1=99, C=100, R1=101, R100=120)
Looking for Fader (Track #4): 110 (0x6E)

### F&F Track #4

Looking for Pan (Track #5): R30, could be 30 (0x1E) or it could be 130 (0x82) (where L100=0, L1=99, C=100, R1=101, R100=120)
Looking for Fader (Track #4): 110 (0x6E)
