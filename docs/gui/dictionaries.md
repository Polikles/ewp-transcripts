# Dictionaries

Use the numbered steps below with the matching GUI stage.

1. Choose dictionary library: Refresh a catalog, add a dictionary file, create a blank dictionary or load the editable example. Removed entries can be shown and restored.
2. View and compare versions: Choose View / edit for an edition. Select a second edition and Compare versions to see changed terms, scope and conventions.
3. Edit a new version: Edit project, scope and entries; keep approved/rejected decisions. Full JSON also exposes manual conventions. Use a new dictionary ID for edits.
4. Save new dictionary version: Save a new immutable edition. Remove from list hides an edition without deleting files referenced by earlier runs. Corpus proposals remain available below.

## 1. Choose dictionary library

Dictionaries are optional. The catalog refreshes automatically when the interface starts; Refresh list remains useful after external changes. Select a library directory, add a dictionary JSON, create a blank dictionary or load the editable example. Choose the kind explicitly: correction of source-language terminology or translation in a particular direction.

## 2. View and compare versions

View / edit opens the selected edition. Select a second edition and Compare versions to inspect changed entries, project scope and conventions. Edition-bearing dictionary ID and content hash distinguish versions; the JSON schema version alone is not an edition number. Expand Show removed dictionaries to restore hidden catalog entries.

## 3. Edit a new version

Edit the project, language/direction, terms and decisions. Full JSON also exposes manual conventions. Preserve approved and rejected entries; rejected mappings must not be sent as approved provider instructions. A dictionary is project context, not a universal spellchecker. Choose a new dictionary ID when saving changed content. Existing canonical text and dictionaries remain unchanged.

The corpus-proposal controls below the editor can compare exact canonical/manual-revision pairs. Review every proposed mapping and mark it approved or rejected before publication. A previous dictionary can carry both decisions forward. This advanced optional route is not required to create a small manual dictionary.

## 4. Save new dictionary version

Save new dictionary version publishes an immutable edition. Duplicate IDs, duplicate source terms or a stale edit base are rejected rather than silently overwritten. Then select that exact edition in correction or translation. Remove from list hides an edition without deleting files referenced by older work; it is reversible.

## Import, export and backup

Export dictionary downloads the selected original JSON independently of user profiles. Add dictionary file validates an imported edition and preserves its bytes, identity and provenance. Importing identical bytes again is safe; different content with the same ID cannot overwrite an existing edition. Edit and save a new ID instead. Back up the library directory or export the required editions. A user profile can optionally embed dictionary files, but does not replace this independent transfer mechanism.
