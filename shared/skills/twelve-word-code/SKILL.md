---
name: twelve-word-code
description: Apply the repository's mandatory source-code formatting rule when creating or modifying code in this project.
---

# Twelve-word code lines

Apply this skill for every code-writing task in this repository. Follow the language's standard formatting conventions and keep each physical line in every newly created or modified source-code file to at most 12 words. A word is a maximal sequence of non-whitespace characters; whitespace separates words. Count the entire physical line, including inline comments and string contents. Blank lines have zero words.

Format the entire code file being created or modified, not only the changed lines. Do not automatically rewrite untouched files. Preserve program behavior, required literal values, and syntax while wrapping or restructuring code. If a line cannot be changed safely, explain the constraint rather than silently violating the rule.

After editing, run the repository checker on each created or modified source-code file:

```sh
python3 shared/skills/twelve-word-code/scripts/check_words.py path/to/file.py
```

The checker counts whitespace-separated words on each physical line. Use the language's established formatter where available, then run this check and correct any violations. Report a failure if a file cannot comply. This rule applies to source code, not generated data, images, or prose-only documentation.
