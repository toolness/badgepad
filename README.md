This is a simple command-line tool to issue badges as static files that
can be served from Apache, Amazon S3, or anything else that serves
static content.

It's inspired by [jeykll][].

## Quick Start

### Setup

This assumes you have [virtualenv][] installed.

```
$ mkdir my-badges
$ cd my-badges
$ virtualenv .virtualenv
$ source .virtualenv/bin/activate
$ pip install -e git://github.com/toolness/badgepad.git#egg=Badgepad
```

### Initialization

At this point, you'll have the `badgepad` command-line tool on your
path. To create the default files and directories for a badgepad
project, run:

```
$ badgepad init
```

Now there should be a file called `config.yml` in your current
directory. Edit it as needed; the `issuer.url` property is
particularly important and determines the domain which your
hosted assertions are tied to.

### Your First Badge Type

First, think of a URL-friendly name (sometimes called a [slug][])
for your badge type. Assuming you've decided to call it `foo`, run:

```
$ badgepad newbadge foo
```

This will create `badges/foo.yml`. Edit that as needed to set the
badge type's metadata and criteria information.

You can also provide an image for the badge type by creating a PNG file
at `badges/foo.png`, e.g.:

```
$ curl http://labs.toolness.com/catbadge.png > badges/foo.png
```

### Issuing A Badge

First, add the recipient to the recipients section of `config.yml`
if needed. For example, you could add the following to the end
of the file:

```
  bar: Bar Jones <bar@jones.com>
```

The name before the colon is a URL-friendly slug for the recipient.

Now, if we want to issue the Foo badge to Bar Jones, we run:

```
$ badgepad issue bar foo
```

This creates `assertions/bar.foo.yml`, which you can edit to provide
issuance metadata and evidence information.

### Building Static Files

All that's left is to build some JSON files and HTML pages and deploy
them to the Web. You can do this by running:

```
$ badgepad build
```

This should output your whole site to the `dist` directory. Deploy that
and make sure it's located at the URL specified by `issuer.url` in your
`config.yml`. Assuming that URL is `http://mybadges.com`, you can now
give Bar Jones a link to `http://mybadges.com/assertions/bar.foo.html`,
where they will be able to see their badge and push it to their
backpack.

## Advanced Usage

Someday I will document how to edit the Jinja2 templates here, and
specify all their context variables.

I will also document all the various metadata properties that can go
into the YAML files.

## Hacking The Source

If you followed the quick start instructions above and want to work on 
badgepad itself, you can find its git repository at
`.virtualenv/src/badgepad`.

  [jekyll]: http://jekyllrb.com/
  [virtualenv]: http://www.virtualenv.org/
  [slug]: http://en.wikipedia.org/wiki/Clean_URL#Slug
