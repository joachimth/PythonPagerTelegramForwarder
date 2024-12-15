# {{ name }}

{{ description }}

**Version:** {{ version }}

**Website:** [Link]({{ website }})

**Maintainer:** {{ maintainer }}


## Instructions

{% for step in instructions.install %}
- {{ step }}
{% endfor %}


## Upgrade Instructions

{% for step in instructions.upgrade %}
- {{ step }}
{% endfor %}
