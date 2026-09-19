"""Focused CLI command registrars with explicit, lazy collaborators.

Each family accepts a frozen Dependencies object supplied by ``cli.create_app``.
The facade owns legacy patch points and passes late-bound callbacks; registrars
import their normal domain types directly and never import the facade. Command
annotations are evaluated when registering so Typer can inspect validators that
close over those supplied dependencies. Importing a registrar performs no runtime
service construction, provider calls, or database access.
"""
