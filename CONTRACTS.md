# JobFinder contracts

## Vacancy identity

- source - source of vacancy
- canonical_url - normalzied URL
- external_id - ...

## Vacancy source

Use just:

- nofluffjobs

## Vacancy field semantic

Required fields:

- `title` - non empty strin;
- `company` - non-empty string;
- `description` - non-empty string;
- `source` - value from `JobSourceEnum`;
- `url` - requiered field;

Oprional field:

- `location` - `None` when the location is unknown;
- `published_at` - `None` whe the publication data is unknow;
- `min_years_experience` - `None` when the requirement is not found;

List fields:

- `skills` - empty list by default;
- `tags` - empty list by default;
- `employment_types` - empty list by default;

An empty string must not be used instead of `None` for optional fields

## CV version semantics

For the MVP, each vacancy has at most one active tailored CV

The tailored CV:

- is generated for a specific vacancy;
- belongs to exactly one job;
- mau replace the previous tailored CV for that job;
- is stored in the `cv_version` table;
- has a file path and creation timestamp;

Historical CV version are not required for the MVP

A full version history may be added later using;

- version nubmer;
- prompt version;
- source CV hash;
- generation timestamp;
- active version flag

## Replacing policy

A successfully processed vacancy must not be processed again automatically

Reprocessing is allowed only whe explicity requested:

- by a manual command;
- by an administartive API endpoint;
- with an explicity `force` or `reprocess` flag

Default behavior:

- if analysis is already completed, keep the existing result;
- if filtering is already completed, keep existing result;
- if tailoring is already completed, keep existing CV;
- do not create duplicate jobs, analyses, matches, or CV versions

When explicit reprocessing is requested:

- update the existing result for the same vacancy;
- do not create a duplicate vanacy;
- record a new processing timestamp

## Pipeline stage states

Each processing stage has an explicit state

Allowed lifecycle:

pending -> processing -> complited

pending -> processing -> failde

analysis:

- pending
- processing
- completed
- failed

filtering:

- pending
- processing
- approved
- rejected
- failed

tailoring:

- pending
- processing
- completed
- failed

Rules:

* `pending` - the stage has not started yet;
* `processing` - the stage is currently running;
* `completed` - the stage finished successfully;
* `approved` - the vacancy passed filtering;
* `filed` - the stage ended with an error;
* state transition must follor the defined lifecycle;
* automatic transitions from terminal states are forbidden;
* automatic reprocessing is forbidden after `completed`, `approved`, `rejected`;
* reprocessing is allowed only when explicity requested with `replaced` or `force`

## Service result DTO

All pipeline services must return a consistent result structure

Required fields:

- `total` - total number of processed items;
- `succeede` - number of successfully processed items;
- `failed` - number of failed items;
- `skipped` - number of skipped items
- `errors` - list of errors with item identifiers and messages

Optional fields:

- `items` - successfully processed result objects;
- `started_at` - processing start timestamp;
- `finished_at` - processing finish timestamp

Invariants:

- `total >= 0`;
- `succeede >= 0`;
- `failed >= 0`;
- `succeede + failed == total`;
- `errors` must contain one entry for every failed item;
- a successfull pipeline execution must not raise an exception for an individual item;
- item-level erros must be collected in `erros`

## Transaction ownership

Repositories own commit and rollback operations

Each vacancy is processed in an independent transaction

A failure for one vacancy must not roll back successfully processed vacancies
