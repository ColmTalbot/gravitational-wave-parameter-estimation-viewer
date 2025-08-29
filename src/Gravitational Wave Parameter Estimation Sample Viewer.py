import marimo

__generated_with = "0.15.2"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    A simple, browser-based, visualiser for gravitational-wave event posteriors.

    This notebook downloads samples released via the gravitational-wave open science center (GWOSC) using `gwsamplefind` and produces one and two-dimensional plots.

    Supported features are:

    - specify one or more events from the gravitational-wave transient catalog (GWTC).
    - specify which parameters samples should be downloaded for.

    Future planned features are:

    - incorporate other event catalogs
    - more complex plots, e.g., skymaps
    """
    )
    return


@app.cell(hide_code=True)
def _():
    import pyodide_http

    pyodide_http.patch_all()

    import altair as alt
    import marimo as mo
    import numpy as np
    import pandas as pd
    from gwsamplefind.client import Client
    return Client, alt, mo, np, pd


@app.cell(hide_code=True)
def _(Client):
    client = Client("https://gwsamples.duckdns.org")
    return (client,)


@app.cell(hide_code=True)
def _(client, mo):
    event_elem = mo.ui.multiselect(
        options=client.events(),
        label="Events:"
    )
    event_elem
    return (event_elem,)


@app.cell(hide_code=True)
def _(event_elem, mo):
    events = event_elem.value

    model_elem = mo.ui.multiselect(
        options=[
           "C01:IMRPhenomXPHM",
           "C01:Mixed",
           "C01:SEOBNRv4PHM",
           "C00:IMRPhenomXPHM-SpinTaylor",
           "C00:SEOBNRv5PHM",
           "C00:NRSur7dq4",
           "C00:IMRPhenomXO4a",
           "C00:Mixed",
           "C00:Mixed+XO4a",
           "C00:IMRPhenomXPHM:LowSpinSecondary",
           "C00:Mixed:LowSpinSecondary",
           "C00:SEOBNRv5PHM:LowSpinSecondary",
           "C01:IMRPhenomPv2_NRTidal:HighSpin",
        ],
        label="Models (ranked order):"
    )

    parameters_elem = mo.ui.multiselect(
        options=[
            "chirp_mass",
            "chirp_mass_source",
            "mass_1",
            "mass_2",
            "mass_1_source",
            "mass_2_source",
            "mass_ratio",
            "a_1",
            "a_2",
            "tilt_1",
            "tilt_2",
            "cos_tilt_1",
            "cos_tilt_2",
            "chi_eff",
            "chi_p",
            "phi_12",
            "phi_jl",
            "luminosity_distance",
            "redshift",
            "theta_jn",
            "cos_theta_jn",
            "ra",
            "dec",
            "phase",
            "psi",
            "geocent_time",
            "H1_time",
            "L1_time",
            "V1_time",
        ],
        label="Parameters:",
    )

    n_samples_elem = mo.ui.slider(
        start=100,
        stop=5000,
        step=100,
        show_value=True,
        include_input=True,
        debounce=True,
        label="N samples:",
    )

    mo.hstack([
        model_elem,
        parameters_elem,
        n_samples_elem,
    ])
    return events, model_elem, n_samples_elem, parameters_elem


@app.cell(hide_code=True)
def _(client, mo):
    @mo.cache
    def get_samples(event, parameters, n_samples, models, seed=123):
        samples = None
        for model in models:
            with mo.status.spinner(
                title=f"Fetching {n_samples} samples for {event}:{model}.",
                subtitle=(
                    f"Parameters: {(', '.join(parameters))}"
                )
            ) as _spinner:
                try:
                    samples = client.get_samples(event=event, parameters=parameters, n_samples=n_samples, seed=123, model=model)
                    break
                except Exception:
                    continue
        if samples is None:
            raise ValueError(f"None of {models} found for {event}")
        return samples
    return (get_samples,)


@app.cell(hide_code=True)
def _(events, mo, model_elem, n_samples_elem, parameters_elem):
    models = model_elem.value
    parameters = parameters_elem.value
    n_samples = n_samples_elem.value

    mo.stop(
        (len(events) == 0) or (len(parameters) == 0) or (len(models) == 0),
        f"Specify event, parameters, and model..."
    )

    fetch_button = mo.ui.run_button(label="Fetch samples")

    fetch_button
    return fetch_button, models, n_samples, parameters


@app.cell(hide_code=True)
def _(events, fetch_button, get_samples, mo, models, n_samples, parameters):
    message = "Click 'Fetch samples' to fetch the samples"

    posts = None

    mo.stop(not fetch_button.value, message)

    posts = [
        get_samples(event=event, parameters=parameters, n_samples=n_samples, seed=123, models=models)[0]
        for event in events
    ]

    mo.accordion({event: post.describe() for event, post in zip(events, posts)})
    return (posts,)


@app.cell(hide_code=True)
def _(mo, parameters):
    one_dimensional_plot_drop = mo.ui.dropdown(
        options=parameters,
        searchable=True,
        label="Parameter:"
    )
    one_dimensional_cumulative = mo.ui.checkbox(
        label=": Cumulative"
    )
    one_dimensional_logx = mo.ui.checkbox(
        label=": log scale x"
    )
    one_dimensional_plot_data = mo.ui.array([
        one_dimensional_plot_drop,
        one_dimensional_cumulative,
        one_dimensional_logx,
    ])

    mo.hstack(one_dimensional_plot_data)
    return (one_dimensional_plot_data,)


@app.cell
def _(alt, events, mo, one_dimensional_plot_data, pd, posts):
    _key, _cumulative, _logx = one_dimensional_plot_data.value

    mo.stop(_key is None)

    _data = pd.DataFrame()
    for _event, _post in zip(events, posts):
        _data[_event] = _post.reset_index()[_key]

    _data_long = _data.melt(var_name="event", value_name="value")

    mo.ui.altair_chart(alt.Chart(_data_long)
        .transform_density("value", groupby=["event"])
        .mark_line()
        .encode(
            x=alt.X("value:Q", title=_key.replace("_", " "), scale=alt.Scale(type="log" if _logx else "linear", domain=[min(_data_long["value"]), max(_data_long["value"])])),
            y=alt.Y("density:Q", title=None),
            color=alt.Color("event:N", title="Event")
    ))
    return


@app.cell(hide_code=True)
def _(mo, parameters, posts):
    two_dimensional_plot_drop_x = mo.ui.dropdown(
        options=parameters,
        label="Horizontal:",
        searchable=True,
    )
    two_dimensional_plot_drop_y = mo.ui.dropdown(
        options=parameters,
        label="Vertical:",
        searchable=True,
    )
    two_dimensional_plot_type = mo.ui.dropdown(
        options=["hexbin", "histogram", "scatter"],
        value="hexbin" if len(posts) == 1 else "scatter",
        label="Plot type:"
    )
    two_dimensional_logx = mo.ui.checkbox(
        label=": log scale x",
        value=False,
    )
    two_dimensional_logy = mo.ui.checkbox(
        label=": log scale y",
        value=False,
    )

    two_dimensional_plot_drop = mo.ui.array(
        [two_dimensional_plot_drop_x, two_dimensional_plot_drop_y],
        label="Parameters:"
    )

    two_dimensional_plot_data = mo.ui.array([
        two_dimensional_plot_drop,
        two_dimensional_plot_type,
        mo.ui.array([
            two_dimensional_logx,
            two_dimensional_logy,
        ]),
    ])

    mo.hstack(two_dimensional_plot_data)
    return (two_dimensional_plot_data,)


@app.cell(hide_code=True)
def _(alt, events, mo, np, pd, posts, two_dimensional_plot_data):
    _x_key, _y_key = two_dimensional_plot_data.value[0]

    mo.stop((_x_key is None or _y_key is None))

    xlim = (np.inf, -np.inf)
    ylim = (np.inf, -np.inf)

    _data = pd.DataFrame(columns=["event", _x_key, _y_key])

    for _event, _post in zip(events, posts):
        _new = _post.reset_index()[[_x_key, _y_key]]
        _new["event"] = _event
        if len(_data) == 0:
            _data = _new
        else:
            _data = pd.concat([_data, _new])

    _logx, _logy = two_dimensional_plot_data.value[2]

    mo.ui.altair_chart(alt.Chart(_data).mark_point().encode(
        x=alt.X(f"{_x_key}:Q", title=_x_key.replace("_", " "), scale=alt.Scale(type="log" if _logx else "linear", domain=[min(_data[_x_key]), max(_data[_x_key])])),
        y=alt.Y(f"{_y_key}:Q", title=_y_key.replace("_", " "), scale=alt.Scale(type="log" if _logy else "linear", domain=[min(_data[_y_key]), max(_data[_y_key])])),
        color=alt.Color("event", title="Event")
    ))
    return


@app.cell(hide_code=True)
def _(mo, parameters):
    scatter_parameters = mo.ui.multiselect(
        options=parameters,
        label="Scatter parameters:",
        searchable=True,
    )

    scatter_parameters
    return (scatter_parameters,)


@app.cell(hide_code=True)
def _(alt, events, mo, pd, posts, scatter_parameters):
    _parameters = scatter_parameters.value

    mo.stop(len(_parameters) == 0)

    _long_posts = list()
    for _post, _event in zip(posts, events):
        _post = _post.reset_index()[_parameters]
        _post["event"] = _event
        _long_posts.append(_post)
    _long_post = pd.concat(_long_posts)

    alt.Chart(_long_post).mark_circle().encode(
        alt.X(alt.repeat("column"), type='quantitative'),
        alt.Y(alt.repeat("row"), type='quantitative'),
        color=alt.Color('event:N', title="Event")
    ).properties(
        width=150,
        height=150
    ).repeat(
        row=_parameters,
        column=_parameters,
    ).interactive()
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
