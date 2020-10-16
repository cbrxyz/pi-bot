# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
* Added a `CHANGELOG.md` file (closing #215)
* Added the `!vc` command (closing #182)

### Fixed
* New tournament channels now enable reading messages by members with the `All Tournaments` role (closing #212)
* Cron list tasks that can not be completed are now skipped (closing #201)