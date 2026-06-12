"""
FitAI - Plotly Charts Module
All chart builder functions for the analytics dashboard.
Returns JSON strings for client-side rendering with Plotly.js.
"""
import json
import plotly.graph_objects as go
import plotly.utils


# Common layout settings
COMMON_LAYOUT = dict(
    template='plotly_dark',
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#e2e8f0', family='Inter, sans-serif', size=13),
    margin=dict(t=40, b=40, l=50, r=20),
    hovermode='x unified',
)

# Color palette
COLORS = {
    'primary': '#7C3AED',
    'secondary': '#06B6D4',
    'success': '#10B981',
    'warning': '#F59E0B',
    'danger': '#EF4444',
    'info': '#3B82F6',
    'primary_alpha': 'rgba(124, 58, 237, 0.15)',
    'secondary_alpha': 'rgba(6, 182, 212, 0.15)',
}


def _to_json(fig):
    """Convert a Plotly figure to JSON string."""
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def create_weight_chart(dates, weights, goal_weight=None):
    """Create weight progress line chart with area fill."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=dates, y=weights,
        mode='lines+markers',
        name='Weight',
        line=dict(color=COLORS['primary'], width=3, shape='spline'),
        marker=dict(size=6, color=COLORS['primary']),
        fill='tozeroy',
        fillcolor=COLORS['primary_alpha'],
        hovertemplate='%{y:.1f} kg<extra></extra>',
    ))

    if goal_weight:
        fig.add_hline(
            y=goal_weight, line_dash='dash',
            line_color=COLORS['success'], line_width=2,
            annotation_text=f'Goal: {goal_weight} kg',
            annotation_font_color=COLORS['success'],
        )

    fig.update_layout(
        **COMMON_LAYOUT,
        title=dict(text='Weight Progress', font=dict(size=16)),
        xaxis=dict(title='Date', gridcolor='rgba(255,255,255,0.05)'),
        yaxis=dict(title='Weight (kg)', gridcolor='rgba(255,255,255,0.05)'),
    )

    return _to_json(fig)


def create_bmi_chart(dates, bmis):
    """Create BMI trend chart with healthy range band."""
    fig = go.Figure()

    # Healthy BMI range band
    fig.add_hrect(
        y0=18.5, y1=24.9,
        fillcolor='rgba(16, 185, 129, 0.08)',
        line=dict(width=0),
        annotation_text='Healthy Range',
        annotation_position='top left',
        annotation_font_color=COLORS['success'],
    )

    fig.add_trace(go.Scatter(
        x=dates, y=bmis,
        mode='lines+markers',
        name='BMI',
        line=dict(color=COLORS['secondary'], width=3, shape='spline'),
        marker=dict(size=6),
        hovertemplate='BMI: %{y:.1f}<extra></extra>',
    ))

    fig.update_layout(
        **COMMON_LAYOUT,
        title=dict(text='BMI Trends', font=dict(size=16)),
        xaxis=dict(title='Date', gridcolor='rgba(255,255,255,0.05)'),
        yaxis=dict(title='BMI', gridcolor='rgba(255,255,255,0.05)'),
    )

    return _to_json(fig)


def create_calories_chart(dates, consumed, burned):
    """Create calories consumed vs burned grouped bar chart."""
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=dates, y=consumed,
        name='Consumed',
        marker_color=COLORS['primary'],
        hovertemplate='%{y:.0f} kcal<extra>Consumed</extra>',
    ))

    fig.add_trace(go.Bar(
        x=dates, y=burned,
        name='Burned',
        marker_color=COLORS['secondary'],
        hovertemplate='%{y:.0f} kcal<extra>Burned</extra>',
    ))

    fig.update_layout(
        **COMMON_LAYOUT,
        barmode='group',
        title=dict(text='Calories: Consumed vs Burned', font=dict(size=16)),
        xaxis=dict(title='Date', gridcolor='rgba(255,255,255,0.05)'),
        yaxis=dict(title='Calories (kcal)', gridcolor='rgba(255,255,255,0.05)'),
        legend=dict(orientation='h', y=-0.15),
    )

    return _to_json(fig)


def create_workout_chart(workout_types, counts, durations=None):
    """Create workout analytics bar chart."""
    fig = go.Figure()

    colors = [COLORS['primary'], COLORS['secondary'], COLORS['success'],
              COLORS['warning'], COLORS['danger'], COLORS['info']]
    bar_colors = [colors[i % len(colors)] for i in range(len(workout_types))]

    fig.add_trace(go.Bar(
        x=workout_types, y=counts,
        name='Sessions',
        marker_color=bar_colors,
        hovertemplate='%{y} sessions<extra></extra>',
    ))

    fig.update_layout(
        **COMMON_LAYOUT,
        title=dict(text='Workout Distribution', font=dict(size=16)),
        xaxis=dict(title='Type', gridcolor='rgba(255,255,255,0.05)'),
        yaxis=dict(title='Sessions', gridcolor='rgba(255,255,255,0.05)'),
    )

    return _to_json(fig)


def create_sleep_chart(dates, hours, qualities=None):
    """Create sleep analytics chart with hours as bars."""
    fig = go.Figure()

    # Color bars by quality if provided
    if qualities:
        quality_map = {'Excellent': COLORS['success'], 'Good': COLORS['info'],
                       'Fair': COLORS['warning'], 'Poor': COLORS['danger']}
        bar_colors = [quality_map.get(q, COLORS['primary']) for q in qualities]
    else:
        bar_colors = COLORS['primary']

    fig.add_trace(go.Bar(
        x=dates, y=hours,
        name='Sleep Hours',
        marker_color=bar_colors,
        hovertemplate='%{y:.1f} hours<extra></extra>',
    ))

    # Recommended sleep line
    fig.add_hline(
        y=8, line_dash='dash',
        line_color=COLORS['success'], line_width=1.5,
        annotation_text='Recommended: 8h',
        annotation_font_color=COLORS['success'],
    )

    fig.update_layout(
        **COMMON_LAYOUT,
        title=dict(text='Sleep Analytics', font=dict(size=16)),
        xaxis=dict(title='Date', gridcolor='rgba(255,255,255,0.05)'),
        yaxis=dict(title='Hours', gridcolor='rgba(255,255,255,0.05)'),
    )

    return _to_json(fig)


def create_water_chart(dates, amounts, goal_ml=2500):
    """Create water intake bar chart with goal line."""
    fig = go.Figure()

    bar_colors = [COLORS['success'] if a >= goal_ml else COLORS['secondary'] for a in amounts]

    fig.add_trace(go.Bar(
        x=dates, y=amounts,
        name='Water Intake',
        marker_color=bar_colors,
        hovertemplate='%{y:.0f} ml<extra></extra>',
    ))

    fig.add_hline(
        y=goal_ml, line_dash='dash',
        line_color=COLORS['warning'], line_width=1.5,
        annotation_text=f'Goal: {goal_ml} ml',
        annotation_font_color=COLORS['warning'],
    )

    fig.update_layout(
        **COMMON_LAYOUT,
        title=dict(text='Water Intake', font=dict(size=16)),
        xaxis=dict(title='Date', gridcolor='rgba(255,255,255,0.05)'),
        yaxis=dict(title='Amount (ml)', gridcolor='rgba(255,255,255,0.05)'),
    )

    return _to_json(fig)


def create_steps_chart(dates, steps, goal_steps=10000):
    """Create step tracking bar chart."""
    fig = go.Figure()

    bar_colors = [COLORS['success'] if s >= goal_steps else COLORS['primary'] for s in steps]

    fig.add_trace(go.Bar(
        x=dates, y=steps,
        name='Steps',
        marker_color=bar_colors,
        hovertemplate='%{y:,.0f} steps<extra></extra>',
    ))

    fig.add_hline(
        y=goal_steps, line_dash='dash',
        line_color=COLORS['warning'], line_width=1.5,
        annotation_text=f'Goal: {goal_steps:,}',
        annotation_font_color=COLORS['warning'],
    )

    fig.update_layout(
        **COMMON_LAYOUT,
        title=dict(text='Daily Steps', font=dict(size=16)),
        xaxis=dict(title='Date', gridcolor='rgba(255,255,255,0.05)'),
        yaxis=dict(title='Steps', gridcolor='rgba(255,255,255,0.05)'),
    )

    return _to_json(fig)


def create_goal_progress_chart(goals):
    """Create horizontal progress bars for goals."""
    if not goals:
        fig = go.Figure()
        fig.update_layout(**COMMON_LAYOUT, title='Goal Progress')
        fig.add_annotation(text='No goals set yet', showarrow=False,
                           font=dict(size=16, color='#64748b'))
        return _to_json(fig)

    goal_names = [f"{g.get('goal_type', 'Goal')} ({g.get('target_value', 0)})" for g in goals]
    progress_values = [g.get('progress', 0) for g in goals]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=progress_values,
        y=goal_names,
        orientation='h',
        marker=dict(
            color=[COLORS['success'] if p >= 100 else COLORS['primary'] for p in progress_values],
        ),
        text=[f'{p:.0f}%' for p in progress_values],
        textposition='inside',
        textfont=dict(color='white', size=14),
        hovertemplate='%{x:.0f}%<extra></extra>',
    ))

    fig.update_layout(
        **COMMON_LAYOUT,
        title=dict(text='Goal Progress', font=dict(size=16)),
        xaxis=dict(range=[0, 105], title='Progress (%)', gridcolor='rgba(255,255,255,0.05)'),
        yaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
    )

    return _to_json(fig)


def create_fitness_score_gauge(score, previous_score=None):
    """Create fitness score gauge indicator."""
    fig = go.Figure(go.Indicator(
        mode='gauge+number' + ('+delta' if previous_score is not None else ''),
        value=score,
        title=dict(text='Fitness Score', font=dict(size=20, color='#e2e8f0')),
        delta=dict(reference=previous_score, increasing=dict(color=COLORS['success']),
                   decreasing=dict(color=COLORS['danger'])) if previous_score is not None else None,
        number=dict(font=dict(size=48, color='#e2e8f0')),
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor='#64748b', tickwidth=1,
                      dtick=20, tickfont=dict(size=12)),
            bar=dict(color=COLORS['primary'], thickness=0.75),
            bgcolor='rgba(0,0,0,0)',
            borderwidth=0,
            steps=[
                dict(range=[0, 33], color='rgba(239, 68, 68, 0.2)'),
                dict(range=[33, 66], color='rgba(245, 158, 11, 0.2)'),
                dict(range=[66, 100], color='rgba(16, 185, 129, 0.2)'),
            ],
            threshold=dict(
                line=dict(color=COLORS['success'], width=3),
                thickness=0.8,
                value=score,
            ),
        ),
    ))

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e2e8f0', family='Inter, sans-serif'),
        margin=dict(t=60, b=20, l=30, r=30),
        height=280,
    )

    return _to_json(fig)


def create_weekly_comparison_chart(this_week, last_week):
    """Create radar chart comparing this week vs last week."""
    categories = list(this_week.keys())
    this_vals = list(this_week.values())
    last_vals = list(last_week.values())

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=this_vals + [this_vals[0]],
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor='rgba(124, 58, 237, 0.15)',
        line=dict(color=COLORS['primary'], width=2),
        name='This Week',
    ))

    fig.add_trace(go.Scatterpolar(
        r=last_vals + [last_vals[0]],
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor='rgba(6, 182, 212, 0.1)',
        line=dict(color=COLORS['secondary'], width=2, dash='dash'),
        name='Last Week',
    ))

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e2e8f0', family='Inter, sans-serif'),
        polar=dict(
            bgcolor='rgba(0,0,0,0)',
            radialaxis=dict(visible=True, gridcolor='rgba(255,255,255,0.08)'),
            angularaxis=dict(gridcolor='rgba(255,255,255,0.08)'),
        ),
        title=dict(text='Weekly Comparison', font=dict(size=16)),
        legend=dict(orientation='h', y=-0.1),
        margin=dict(t=60, b=40, l=60, r=60),
    )

    return _to_json(fig)


def create_calorie_trend_chart(dates, net_calories):
    """Create calorie surplus/deficit area chart."""
    fig = go.Figure()

    colors = [COLORS['success'] if c <= 0 else COLORS['danger'] for c in net_calories]

    fig.add_trace(go.Bar(
        x=dates, y=net_calories,
        marker_color=colors,
        name='Net Calories',
        hovertemplate='%{y:+.0f} kcal<extra></extra>',
    ))

    fig.add_hline(y=0, line_color='#64748b', line_width=1)

    fig.update_layout(
        **COMMON_LAYOUT,
        title=dict(text='Calorie Balance (Surplus/Deficit)', font=dict(size=16)),
        xaxis=dict(title='Date', gridcolor='rgba(255,255,255,0.05)'),
        yaxis=dict(title='Net Calories', gridcolor='rgba(255,255,255,0.05)'),
    )

    return _to_json(fig)
