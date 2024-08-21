{include} ../README.md
# My nifty title

Some **text**!

:::{admonition} Here's my title
:class: tip

Here's my admonition content.{sup}`1`
:::

(header-label)=
# A header

[My rehference](#header-label)

### Content
```{toctree}
:maxdepth: 2

Home <self>
apidocs/index
```

```{autodoc2-object} githubapp.events.event.Event
render_plugin = "myst"
no_index = true
```

