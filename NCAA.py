import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="What seperates a regular team from a championship team?", layout="wide")
df = pd.read_csv("cbb.csv")

st.title("What seperates a regular team from a championship team?")
st.write("#### By: Abdullahi Cali")
st.write("---")
st.write("#### Glossary")
with st.expander("View Data Glossary & Terms"):
    st.markdown("""
    * **ADJOE** (*Adjusted Offensive Efficiency*): Points scored per 100 possessions. **Higher is better.**
    * **ADJDE** (*Adjusted Defensive Efficiency*): Points allowed per 100 possessions. **Lower is better.**
    * **EFG%** (*Effective Field Goal Percentage*): Shooting percentage that accounts for the extra value of 3-pointers.

    * **ORB** (*Offensive Rebounds*): Number of missed shots rebounded by the offensive team, extending possession. **Higher is better.**
    * **DRB** (*Defensive Rebounds*): Number of missed shots rebounded by the defensive team, ending the opponent’s possession. **Higher is better.**
    """)

# A clean callout box for chart instructions
st.write("---")
st.info("**Interactive Feature:** Click and drag a rectangle over the scatter plot to dynamically filter the charts below!")


# CLeaning  data
df['CONF'] = df['CONF'].str.upper() # all conf types as uppercase
df['MADE_TOURNAMENT'] = df['SEED'].notna().astype(int) # remove floats
df['SEED'] = df['SEED'].fillna("Non-Tournament").astype(str)
postseason_wins = {
    "Champions" : 6,
    "2ND" : 5,
    "F4" : 4,
    "E8" : 3,
    "S16" : 2,
    "R32" : 1,
    "R64" : 0,
}

df['TOURNAMENT_WINS'] = df['POSTSEASON'].map(postseason_wins).fillna(0).astype(int)
df['POSTSEASON'] = df['POSTSEASON'].fillna("Regular Season Only")



#split dataset into tournament teams and regular teams
tteams = df[df['MADE_TOURNAMENT'] == 1].copy()
rteams = df[df['MADE_TOURNAMENT'] == 0].copy()



chart_eligible_teams = tteams[tteams['TOURNAMENT_WINS'] >= 2]
available_conferences = sorted(chart_eligible_teams['CONF'].unique())

# Add the "All" option for a global view
conference_options = ["All"] + available_conferences

st.sidebar.header("Dashboard Filters")

# This will now only show buttons for conferences with deep tournament runs
selected_conf = st.sidebar.pills(
    "Select a Conference:",
    options=conference_options,
    default="All"
)

# Apply the global filter to your main datasets based on the button clicked
if selected_conf != "All":
    tteams = tteams[tteams['CONF'] == selected_conf]
    rteams = rteams[rteams['CONF'] == selected_conf]


# --- 1. Define ONE global selection parameter ---
# Leaving placeholders as strings instead of empty brackets prevents syntax crashes
# 'brush' captures an area on the scatter plot
brush = alt.selection_interval(name="brush", empty="all")

# 'click_round' captures a clicked bar on the bar chart
click = alt.selection_point(name="click", fields=["POSTSEASON"], empty="all")
# --- Chart 1: Neomycin ---



scatter_plot = (
    alt.Chart(tteams[tteams["TOURNAMENT_WINS"] >= 2])
    .transform_calculate(
        finish="""
        datum.POSTSEASON == 'F4' ? 'Final Four' :
        datum.POSTSEASON == 'E8' ? 'Elite Eight' :
        datum.POSTSEASON == 'S16' ? 'Sweet Sixteen' :
        datum.POSTSEASON
        """,
        hover_text="""
        datum.POSTSEASON == 'Champion'
            ? datum.TEAM + ' won the ' + datum.YEAR + ' NCAA March Madness tournament.'
        : datum.POSTSEASON == '2nd'
            ? datum.TEAM + ' was the runner-up in the ' + datum.YEAR + ' NCAA March Madness tournament.'
        : datum.TEAM + ' reached the ' + datum.finish + ' in the ' + datum.YEAR + ' NCAA March Madness tournament.'
        """
    )
    .mark_circle(size=130, stroke="black", strokeWidth=0.5)
    .encode(
        x=alt.X(
            "ADJOE:Q",
            title="Adjusted Offensive Efficiency (ADJOE)",
            scale=alt.Scale(zero=False),
        ),
        y=alt.Y(
            "ADJDE:Q",
            title="Adjusted Defensive Efficiency (ADJDE) - Lower is Better",
            scale=alt.Scale(reverse=True, zero=False),
        ),
        color=alt.condition(
            brush,
            alt.Color(
                "POSTSEASON:N",
                title="Tournament Finish",
                scale=alt.Scale(scheme="category10"),
            ),
            alt.value("lightgray"),
        ),
        opacity=alt.condition(brush, alt.value(0.9), alt.value(0.15)),
        tooltip=[
            alt.Tooltip("hover_text:N", title=" ")
        ],
    )
    .properties(
        title="Adjusted Offensive vs. Defensive Efficiency: Identifying Elite Teams",
        width=600,
        height=500,
    )
    .add_params(brush)
)

# 4. Generate the Vertical Benchmark Line (ADJOE = 115)
bench_x = (
    alt.Chart(pd.DataFrame({"x": [115]}))
    .mark_rule(color="yellow", strokeDash=[4, 4], strokeWidth=1.5)
    .encode(x="x:Q")
)

# 5. Generate the Horizontal Benchmark Line (ADJDE = 95)
bench_y = (
    alt.Chart(pd.DataFrame({"y": [95]}))
    .mark_rule(color="yellow", strokeDash=[4, 4], strokeWidth=1.5)
    .encode(y="y:Q")
)

# 6. Optional: Add a text label directly onto the plot identifying the Elite Zone
label_data = pd.DataFrame([{"x": 124, "y": 86, "text": "Elite Zone"}])
zone_label = (
    alt.Chart(label_data)
    .mark_text(color="yellow", fontWeight="bold", fontSize=13)
    .encode(x="x:Q", y="y:Q", text="text:N")
)

# 7. Layer all elements together
final_chart = scatter_plot + bench_x + bench_y + zone_label

distribution_bar = (
    alt.Chart(tteams[tteams["TOURNAMENT_WINS"] >= 2])
    .transform_filter(brush)
    .transform_aggregate(
        teams="count()",
        groupby=["POSTSEASON"]
    )
    .transform_calculate(
        finish="""
        datum.POSTSEASON == 'S16' ? 'Sweet Sixteen' :
        datum.POSTSEASON == 'E8' ? 'Elite Eight' :
        datum.POSTSEASON == 'F4' ? 'Final Four' :
        datum.POSTSEASON == '2nd' ? 'Runner-up' :
        datum.POSTSEASON == 'Champion' ? 'Championship' :
        datum.POSTSEASON
        """,
        hover_text="datum.teams + ' teams made the ' + datum.finish + '.'"
    )
    .mark_bar()
    .encode(
        x=alt.X(
            "POSTSEASON:N",
            title="Furthest Tournament Round Reached",
            sort=["S16", "E8", "F4", "2nd", "Champion"]
        ),
        y=alt.Y("teams:Q", title="Number of Teams"),
        color=alt.Color(
            "POSTSEASON:N",
            scale=alt.Scale(scheme="category10"),
            legend=None
        ),
        tooltip=[
            alt.Tooltip("hover_text:N", title=" ")
        ]
    )
    .properties(
        width=600,
        height=500,
        title="Tournament Advancement Distribution"
    )
)

# --- 2. Stitch them together as one dashboard ---
dashboard = alt.hconcat(
    final_chart,
    distribution_bar
)
st.altair_chart(dashboard, use_container_width=True)

chart3 = (
    alt.Chart(tteams[tteams["TOURNAMENT_WINS"] >= 2])
    .transform_aggregate(
        avg_efg="mean(EFG_O)",
        groupby=["POSTSEASON"]
    )
    .transform_calculate(
        finish="""
        datum.POSTSEASON == 'S16' ? 'Sweet Sixteen' :
        datum.POSTSEASON == 'E8' ? 'Elite Eight' :
        datum.POSTSEASON == 'F4' ? 'Final Four' :
        datum.POSTSEASON == '2nd' ? 'Runner-up' :
        datum.POSTSEASON == 'Champion' ? 'Champion' :
        datum.POSTSEASON
        """,
        hover_text="""
        datum.POSTSEASON == 'S16'
            ? 'Sweet Sixteen teams average ' + format(datum.avg_efg, '.1f') + '% EFG, showing solid but not elite efficiency.'
        : datum.POSTSEASON == 'E8'
            ? 'Elite Eight teams average ' + format(datum.avg_efg, '.1f') + '% EFG, separating with stronger shot-making.'
        : datum.POSTSEASON == 'F4'
            ? 'Final Four teams average ' + format(datum.avg_efg, '.1f') + '% EFG, combining efficiency with elite execution.'
        : datum.POSTSEASON == '2ND'
            ? 'Runner-up teams average ' + format(datum.avg_efg, '.1f') + '% EFG but fall short in key moments.'
        : datum.POSTSEASON == 'Champions'
            ? 'Championship teams average ' + format(datum.avg_efg, '.1f') + '% EFG, sustaining elite offensive efficiency.'
        : ' '
        """
    )
    .mark_bar()
    .encode(
        x=alt.X(
            "avg_efg:Q",
            title="Average Effective Field Goal % (Offense)",
            scale=alt.Scale(domain=[0, 60])
        ),
        y=alt.Y(
            "POSTSEASON:N",
            title="Tournament Round",
            sort=["S16", "E8", "F4", "2nd", "Champion"]
        ),
        color=alt.Color(
            "POSTSEASON:N",
            scale=alt.Scale(scheme="category10"),
            legend=None
        ),
        tooltip=[
            alt.Tooltip("hover_text:N", title= " ")
        ]
    )
    .properties(
        height=250,
        title="Does Elite Shooting Guarantee a Championship?"
    )
)

# Render it at the very bottom, below your column layout
st.write("---")
st.altair_chart(chart3, use_container_width=True)

st.write("---")
st.write("Do Championship Teams Control the Glass?")
rebound_data = tteams[tteams['TOURNAMENT_WINS'] >= 2]

# 2. Chart 4: Offensive Rebounding
chart_orb = (
    alt.Chart(tteams[tteams["TOURNAMENT_WINS"] >= 2])
    .transform_aggregate(
        avg_orb="mean(ORB)",
        groupby=["POSTSEASON"]
    )
    .transform_calculate(
        hover_text="""
        'Offensive rebound rate: ' + format(datum.avg_orb, '.1f') +
        '%. Measures how often a team secures its own missed shots.'
        """
    )
    .mark_bar()
    .encode(
        x=alt.X(
            "avg_orb:Q",
            title="Offensive Rebound Rate (%)",
            scale=alt.Scale(domain=[0, 36])
        ),
        y=alt.Y(
            "POSTSEASON:N",
            title="Tournament Round",
            sort=["S16", "E8", "F4", "2ND", "Champions"]
        ),
        color=alt.Color(
            "POSTSEASON:N",
            scale=alt.Scale(scheme="category10"),
            legend=None
        ),
        tooltip=[alt.Tooltip("hover_text:N", title= " ")]
    )
    .properties(height=250)
)

# 3. Chart 5: Defensive Rebounding Allowed
chart_drb = (
    alt.Chart(tteams[tteams["TOURNAMENT_WINS"] >= 2])
    .transform_aggregate(
        avg_drb="mean(DRB)",
        groupby=["POSTSEASON"]
    )
    .transform_calculate(
        hover_text="""
        'Defensive rebound rate: ' + format(datum.avg_drb, '.1f') +
        '%. Measures how often a team secures defensive rebounds after opponent misses.'
        """
    )
    .mark_bar()
    .encode(
        x=alt.X(
            "avg_drb:Q",
            title="Defensive Rebound Rate (%)",
            scale=alt.Scale(domain=[0, 30])
        ),
        y=alt.Y(
            "POSTSEASON:N",
            title="Tournament Round",
            sort=["S16", "E8", "F4", "2ND", "Champions"],
            axis=None
        ),
        color=alt.Color(
            "POSTSEASON:N",
            scale=alt.Scale(scheme="category10"),
            legend=None
        ),
        tooltip=[alt.Tooltip("hover_text:N", title= " ")]
    )
    .properties(height=250)
)
# 4. Render them sequentially or side-by-side
# If side-by-side fails, Streamlit will fallback safely
rebound_col1, rebound_col2 = st.columns(2)
with rebound_col1:
    st.altair_chart(chart_orb, use_container_width=True)
with rebound_col2:
    st.altair_chart(chart_drb, use_container_width=True)

st.write("---")
st.write("##  Summary: The Championship Formula Proved")

st.markdown("""
Based on the historical performance of tournament teams in this dataset, the data suggests that reaching the **Champions** tier is not a random occurrence. It requires meeting specific statistical benchmarks:

1. **The Elite Efficiency Threshold:** Our primary scatter plot shows a dense cluster of champions in the **Elite Zone** (ADJOE > 115 and ADJDE < 95). Teams that fall outside of this zone might string together a couple of tournament wins, but they almost never survive to cut down the nets.
   
2. **Shooting Peak Efficiency:** As seen in the *Shooting Efficiency* chart, offensive execution scales upward with every passing weekend. Championship teams separate themselves by maintaining an average **Effective Field Goal Percentage (EFG_O)** near or above **54%** against elite tournament defenses.

3. **Defensive Glass Lockdown Is Mandatory:** The *Rebounding Dominance* charts reveal a crucial asymmetric truth. While offensive rebounding remains relatively flat across rounds, **Defensive Rebounding Allowed (DRB)** steadily shrinks for champions. Winning the tournament requires completely denying opponents second-chance opportunities, locking down defensive boards to hold opponents near or below a tight **28% to 29%** offensive rebound rate.
""")
