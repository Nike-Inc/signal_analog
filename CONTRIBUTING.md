# Contributing

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

You can contribute in many ways:

## Types of Contributions

### Report Bugs

If you are reporting a bug, please include:

-   Your operating system name and version.
-   Any details about your local setup that might be helpful
    in troubleshooting.
-   Detailed steps to reproduce the bug.

### Fix Bugs

[Look through our issues] on GitHub. Anything tagged with
a "bug" ticket type is open to whoever wants to implement it.

### Implement Features

[Look through our issues] on GitHub. Anything tagged with "enhancement"
and "help wanted" is open to whoever wants to implement it.

### Write Documentation

Signal Analog could always use more documentation, whether as part of the
official Signal Analog docs, in docstrings, or even on the web in blog posts,
articles, and such.

### Submit Feedback

If you are proposing a feature:

-   Explain in detail how it would work.
-   Keep the scope as narrow as possible, to make it easier
    to implement.
-   Remember that this is a volunteer-driven project, and that
    contributions are welcome :)

## Get Started!

Ready to contribute? Here's how to set up `signal_analog` for local
development.

1.  Fork the `signal_analog` repo on GitHub.
2.  Clone your fork locally:

        $ git clone ssh://git@github.com:Nike-inc/signal_analog.git

3.  Install your local copy into a virtualenv. Assuming you have
    at least python3 installed:

        $ cd signal_analog/
        $ python3 -m venv venv
        $ source venv/bin/activate
        $ pip install -r requirements_dev.txt

4.  Create a branch for local development:

        $ git checkout -b feature/name-of-your-feature

    Or if creating a bugfix

        $ git checkout -b fix/name-of-your-bugfix

    Now you can make your changes locally.

5.  When you're done making changes, check that your changes pass tests,
    including testing other Python versions with tox:

        $ make test-all

6.  Also be sure to check your code against PEP8 rules:

        $ make lint

6.  Commit your changes and push your branch to BitBucket:

        $ git add .
        $ git commit -m "Your detailed description of your changes."
        $ git push origin name-of-your-bugfix-or-feature

7.  Submit a pull request through the BitBucket website.

## Pull Request Guidelines

Before you submit a pull request, check that it meets these guidelines:

1.  The pull request should include tests.
2.  If the pull request adds functionality, the docs should be updated.
    Put your new functionality into a function with a docstring, and add
    the feature to the list in README.md.
3.  The pull request should work for Python 2.7+ and 3.6+.
4.  New changes should be added to CHANGELOG.md

## Tips

To run a subset of tests:

    $ py.test tests.test_signal_analog


[Look through our issues]: https://github.com/Nike-inc/signal_analog/issues
