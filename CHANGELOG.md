# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 4.4.41 - 2020-11-19
### Added
* `!forums` now sends a link to the Scioly.org forums (closes [#284](https://github.com/cbrxyz/pi-bot/issues/284))

### Changed
* Members can now run specific allowed commands outside of `#bot-spam` (closes [#275](https://github.com/cbrxyz/pi-bot/issues/275))

## 4.4.40 - 2020-11-18
### Added
* `!userfromid` to get a user from specified ID (closes [#283](https://github.com/cbrxyz/pi-bot/issues/283))

## 4.4.39 - 2020-11-17
### Changed
* Bot statuses are now stored in array instead of long conditional (closes [#174](https://github.com/cbrxyz/pi-bot/issues/174))

## 4.4.38 - 2020-11-15
### Added
* Added the `!magic8ball` command (closes [#272](https://github.com/cbrxyz/pi-bot/issues/272))

### Fixed
* Commands now work in DM's again (closes [#278](https://github.com/cbrxyz/pi-bot/issues/278))

## 4.4.37 - 2020-11-14
### Added
* Simple `!xkcd` command (closes [#181](https://github.com/cbrxyz/pi-bot/issues/181))

## 4.4.36 - 2020-11-13
### Added
* `!list all` now shows pages of commands separately (closes [#187](https://github.com/cbrxyz/pi-bot/issues/187))

## 4.4.35 - 2020-11-12
### Changed
* Calling `!tag example` where `example` is a legitimate tag will delete the original message (closes [#274](https://github.com/cbrxyz/pi-bot/issues/274))
* Commands run by members in channels other than `#bot-spam` will now not be processed and will direct the user to the appropriate channel. (closes [#219](https://github.com/cbrxyz/pi-bot/issues/219))

### Fixed
* Typo in `!stealfish` (closes [#273](https://github.com/cbrxyz/pi-bot/issues/273))

## 4.4.34 - 2020-11-11
### Fixed
* `!nuke n` would throw an error if the user attempted to delete `-n` messages when `n` was larger than the number of messages in the channel

## 4.4.33 - 2020-11-11
### Added
* `!nuke` now accepts negative indexes to delete all but last n messages (closes [#271](https://github.com/cbrxyz/pi-bot/issues/271))

### Fixed
* Deletion needed reports for tournament channels would occur despite tournament channels not needing to be deleted (closes [#270](https://github.com/cbrxyz/pi-bot/issues/270))

## 4.4.32 - 2020-11-10
### Added
* Documentation for `!tag` added (closes [#265](https://github.com/cbrxyz/pi-bot/issues/265))

### Changed
* When user sends link to external Discord server, a warning is now displayed explaining why the message was censored (closes [#267](https://github.com/cbrxyz/pi-bot/issues/267))

## 4.4.31 - 2020-11-07
### Fixed
* `!wiki pageName` where `pageName` is not a valid page name now shows proper error (closes [#257](https://github.com/cbrxyz/pi-bot/issues/257))
* `!wiki link pageName` was fixed to actually link to `pageName` (closes [#256](https://github.com/cbrxyz/pi-bot/issues/256))
* Wiki URLs now accurately link to page titles containing ":" or "/" (closes [#161](https://github.com/cbrxyz/pi-bot/issues/161))

## 4.4.30 - 2020-11-06
### Added
* `!tag` command, which references the Tags spreadsheet (closes [#253](https://github.com/cbrxyz/pi-bot/issues/253))

## 4.4.29 - 2020-11-05
### Changed
* `!wiki` with no other arguments now sends link to the wiki homepage (closes [#189](https://github.com/cbrxyz/pi-bot/issues/189))
* `!wiki [page_name]` will now assume `!wiki link [page_name]` (closes [#231](https://github.com/cbrxyz/pi-bot/issues/231))
* `!wiki` will now report too many arguments given when there are more than 7 arguments

### Fixed
* Edited message log fields are now capped at 1024 characters, which will hopefully result in many less error messages regarding overflowing edited message logs

## 4.4.28 - 2020-11-04
### Added
* `!graphscilympiad` command added to make a graph of Scilympiad final results (closes [#243](https://github.com/cbrxyz/pi-bot/issues/243))

### Changed
* `!tournament` now ignores commonly used words to cut down on mistaken reports (closes [#250](https://github.com/cbrxyz/pi-bot/issues/250))
* `async def list()` command was renamed to `async def list_command()` in code to avoid overwriting built-in `list()` function

## 4.4.27 - 2020-11-03
### Added
* Added `!rule` command for quickly displaying a rule (closes [#200](https://github.com/cbrxyz/pi-bot/issues/200))

### Removed
* Removed `!invites` command, which led to nothing

## 4.4.26 - 2020-11-02
### Added
* Commandinfo for each command can now support flags (closes [#29](https://github.com/cbrxyz/pi-bot/issues/29))

## 4.4.25 - 2020-11-01
### Changed
* Changed `CATEGORY_TOURNAMENTS` name to lowercase `tournaments` for standardization

## 4.4.24 - 2020-11-01
### Changed
* `!wikipedia` terms with multiple words now do not need quotes (closes [#241](https://github.com/cbrxyz/pi-bot/issues/241))
* `!wikipedia` with no function term will now assume the `link` function (ex, `!wp red bear` now assumes `!wp link red bear`)

## 4.4.23 - 2020-10-31
### Changed
* `!help` with no other arguments now shows special message (closes [#140](https://github.com/cbrxyz/pi-bot/issues/140))

## 4.4.22 - 2020-10-30
### Changed
* `#member-leave` messages now show if user was unconfirmed and when they joined. (closes [#237](https://github.com/cbrxyz/pi-bot/issues/237))

## 4.4.21 - 2020-10-29
### Added
* Added `!rand` command to generate random numbers (closes [#199](https://github.com/cbrxyz/pi-bot/issues/199))

## 4.4.20 - 2020-10-28
### Added
* Added `!resultstemplate` command to make a results template from raw Scilympiad results (closes [#244](https://github.com/cbrxyz/pi-bot/issues/244))

## 4.4.19 - 2020-10-27
### Fixed
* Bot now uses Intents

## 4.4.18 - 2020-10-27
### Fixed
* Fixed ping issues with censor (closes [#222](https://github.com/cbrxyz/pi-bot/issues/222))

## 4.4.17 - 2020-10-26
### Added
* `!vc` now works for `#games` (closes [#245](https://github.com/cbrxyz/pi-bot/issues/245))

## 4.4.16 - 2020-10-24
### Fixed
* Fixed typo in the name of "They / Them / Theirs" role (closes [#240](https://github.com/cbrxyz/pi-bot/issues/240))

## 4.4.15 - 2020-10-23
### Fixed
* Tournaments list showed channels opening in 0 days.

## 4.4.14 - 2020-10-22
### Added
* Global variables for server variables (such as the names of all roles and channels) (closes [#232](https://github.com/cbrxyz/pi-bot/issues/232))

## 4.4.13 - 2020-10-21
### Changed
* Requested tournaments list now uses middle dot symbol rather than dash to separate command and number of votes (closes [#233](https://github.com/cbrxyz/pi-bot/issues/233))
* `!list` now shows commands in alphabetical order (closes [#235](https://github.com/cbrxyz/pi-bot/issues/235))

## 4.4.12 - 2020-10-20
### Changed
* Tournament list is formatted cleaner (closes [#230](https://github.com/cbrxyz/pi-bot/issues/230))
* `!pronouns` help message is now formatted cleaner (closes [#142](https://github.com/cbrxyz/pi-bot/issues/142))

### Fixed
* Member leave messages no longer mention users, as this can break after user has left the server (closes [#229](https://github.com/cbrxyz/pi-bot/issues/229))

## 4.4.11 - 2020-10-17
### Fixed
* `#server-support` mentions renamed to `#site-support`

## 4.4.10 - 2020-10-16
### Changed
* `!mute`, `!ban`, and `!selfmute` now display times in Eastern time.
* Tournament voting commands are now shown next to proposed tournament channels.

### Fixed
* `!me` called with no arguments now deletes original message.
* `!list` fixed for regular members.

## 4.4.9 - 2020-10-15
### Added
* Log member leave events to `#member-leave` channel.

## 4.4.8 - 2020-10-14
### Changed
* Hotfix for `!selfmute` being broken for all members.

## 4.4.7 - 2020-10-14
### Changed
* `!selfmute` now sends an error message when staff members run the command, as the command will not work for them.
* Messages needed to mute for caps changed from 6 to 8.

## 4.4.6 - 2020-10-08
### Added
* Added the `!graphpage` command to assist in graphing wiki pages. For example, `!graphpage "2020 New Jersey State Tournament" Y 1 C` to graph the Division C chart for that state tournament.

### Changed
* Updated `.gitignore` to avoid including `.svg` files in version control as they are often temporary files.

## 4.4.5 - 2020-10-07
### Added
* Added a `CHANGELOG.md` file (closing [#215](https://github.com/cbrxyz/pi-bot/issues/215))
* Added the `!vc` command (closing [#182](https://github.com/cbrxyz/pi-bot/issues/182))

### Fixed
* New tournament channels now enable reading messages by members with the `All Tournaments` role (closing [#212](https://github.com/cbrxyz/pi-bot/issues/212))
* Cron list tasks that can not be completed are now skipped (closing [#201](https://github.com/cbrxyz/pi-bot/issues/201))