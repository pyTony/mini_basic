# BASIC applications

## Number Guessing Game

`number_guessing.bas` chooses a number from 1 through 100 and gives
`TOO LOW` or `TOO HIGH` hints until the player finds it. It counts guesses,
rejects values outside the range, and offers another round.

Run it from the `cport` directory:

```powershell
.\mbasic.exe examples\apps\number_guessing.bas
```

Answer the replay prompt with uppercase `Y` or `N`.

## Hangman

`hangman.bas` selects from a hardcoded list of 50 words. It displays the
partially guessed word, tracks used letters, rejects duplicate and
multi-character guesses, and draws the six-stage hangman.

```powershell
.\mbasic.exe examples\apps\hangman.bas
```

Letter guesses and replay answers are case-insensitive.

## Rock-Paper-Scissors

`rock_paper_scissors.bas` plays repeated rounds against the computer,
validates choices, and tracks player wins, computer wins, and ties.

```powershell
.\mbasic.exe examples\apps\rock_paper_scissors.bas
```

Choices and replay answers are case-insensitive. Enter `QUIT` at the choice
prompt to finish and display the final score.

## Password Generator

`password_generator.bas` creates passwords from uppercase letters,
lowercase letters, digits, and optionally symbols. It accepts lengths from
4 through 40 and can generate multiple passwords.

```powershell
.\mbasic.exe examples\apps\password_generator.bas
```

Prompts are case-insensitive. This is a programming demonstration, not a
cryptographically secure password generator: the interpreter's `RND`
function is deterministic and is not suitable for protecting real
accounts.

## Caesar Cipher Tool

`caesar_cipher.bas` encodes and decodes text with a shift from 0 through
25. It preserves uppercase and lowercase letters and leaves spaces,
numbers, and punctuation unchanged.

```powershell
.\mbasic.exe examples\apps\caesar_cipher.bas
```

Mode commands are case-insensitive. Caesar ciphers are educational and
provide no meaningful security.
