import streamlit as st
import pandas as pd
import numpy as np

# Page config
st.set_page_config(page_title="Active User Fee Earnings", layout="wide")
st.title("🚀 Active User Fee Earnings")

# --- Pull simulation settings from main page ---
try:
    initial_xtokens = st.session_state.initial_xtokens
    locked_tokens = st.session_state.locked_tokens
    initial_price = st.session_state.initial_price
    weekly_fees = st.session_state.weekly_fees
    base_emission = st.session_state.base_emission
    decay_percent = st.session_state.decay_percent
    weeks = st.session_state.weeks
except AttributeError:
    st.error("⚠️ Please visit the main page first to set the tokenomics parameters.")
    st.stop()

# --- Sidebar inputs ---
with st.sidebar:
    st.header("Active User Settings")

    my_tokens = st.number_input("Your Token Holdings", value=10_000, format="%d")

    voting_tokens = st.number_input("Tokens for Voting on Fees", value=3000, step=100)
    multiplier_tokens = st.number_input("Tokens for Multiplier Staking", value=3000, step=100)

    # Remaining tokens used for hatching
    volume_tokens = my_tokens - voting_tokens - multiplier_tokens

    if volume_tokens < 0:
        st.error("⚠️ The total allocation exceeds your token holdings. Please adjust.")
        st.stop()

    st.markdown(f"**Tokens for Hatching (Unused)**: {volume_tokens} tokens")
    st.markdown(f"**Total Value:** ${my_tokens * initial_price:,.2f}")

# --- Simulation setup ---
weeks_array = np.arange(weeks)
decay_rate = 1 - (decay_percent / 100)
weekly_emissions = base_emission * (decay_rate ** weeks_array)
cumulative_emissions = np.cumsum(weekly_emissions)
circulating_supply = initial_xtokens + cumulative_emissions

# --- Multiplier Growth ---
# Multiplier increases with time: 1.05^week, simulating progressive boosting
multiplier_growth = 1.05 ** weeks_array

# --- Voting Fee Calculation ---
voting_share = voting_tokens / circulating_supply
voting_weekly_fees = voting_share * weekly_fees
user_cumulative_fees = np.cumsum(voting_weekly_fees)
relative_pct = (user_cumulative_fees / (my_tokens * initial_price)) * 100

# --- Plot: Cumulative Voting Fees ---
st.subheader("📊 Cumulative Voting Fees")
st.line_chart(user_cumulative_fees)

# --- Volume Emissions Inputs ---
st.subheader("📦 Emissions from Trading Volume (Multiplier Asset)")

col1, col2, col3 = st.columns(3)
with col1:
    asset_weight = st.number_input("Asset Weight (% of Total Emissions)", value=10.0, step=0.5) / 100
with col2:
    total_volume = st.number_input("Total Volume on Asset ($)", value=100_000_000, step=1_000_000)
with col3:
    user_volume = st.number_input("Your Weekly Volume ($)", value=2_000_000, step=100_000)

# --- Volume Emissions Logic ---
# Base asset emissions (10% of total emissions)
asset_weekly_emissions = weekly_emissions * asset_weight

# Reference stake (for the pool)
reference_stake = 5000
user_stake = multiplier_tokens

# Multiplier logic: Each week, effective stake = stake * (1.05^week)
effective_stake = user_stake * multiplier_growth

# Calculate multiplier: 1 + ratio * 3, where ratio = effective_stake / (effective_stake + reference_stake)
stake_ratio = effective_stake / (effective_stake + reference_stake)
effective_multiplier = 1 + stake_ratio * 3

# Effective volume per week: user_volume * multiplier
effective_volume = user_volume * effective_multiplier

# Adjusted total volume = original total - user volume + effective volume
adjusted_total_volume = total_volume - user_volume + effective_volume

# User share of volume-based emissions
user_share_of_volume = effective_volume / adjusted_total_volume
user_weekly_rewards = user_share_of_volume * asset_weekly_emissions
user_cumulative_rewards = np.cumsum(user_weekly_rewards)

# --- No-multiplier baseline (for comparison) ---
baseline_effective_volume = np.full(weeks, user_volume)
baseline_total_volume = total_volume
baseline_share = baseline_effective_volume / baseline_total_volume
baseline_rewards = baseline_share * asset_weekly_emissions

# --- Data Aggregation ---
df = pd.DataFrame({
    "Week": weeks_array,
    "Voting Weekly Fees": voting_weekly_fees,
    "Cumulative Voting Fees": user_cumulative_fees,
    "Relative Voting Earnings (%)": relative_pct,
    "Volume Weekly Rewards": user_weekly_rewards,
    "Cumulative Volume Rewards": user_cumulative_rewards,
    "Baseline Volume Rewards (No Multiplier)": np.cumsum(baseline_rewards),
    "Multiplier": effective_multiplier
}).set_index("Week")

# --- Plot Volume Emissions ---
st.subheader("📈 Cumulative Volume-Based Rewards")
st.line_chart(df[["Cumulative Volume Rewards", "Baseline Volume Rewards (No Multiplier)"]])

# --- ROI Plot ---
st.subheader("💸 Relative ROI from Voting Over Time (%)")
st.line_chart(df["Relative Voting Earnings (%)"])

# --- Explanation ---
st.markdown("""
### 🧠 Calculation Logic

- **Voting Rewards**: Your voting tokens are divided by circulating supply each week to determine share of the $weekly_fees.
- **Volume Emissions**:
    - 10% of the weekly emissions go to a specific trading asset.
    - The user earns a share of these emissions based on their *effective volume*, boosted by their multiplier.
    - Multiplier: `1 + 3 * (effective stake / (effective stake + reference stake))` where `effective stake = stake * 1.05^week`
    - Adjusted total volume accounts for your boosted volume replacing your original share.
- **Comparison**: The chart shows how your rewards compare to no multiplier at all.
""")

# --- Data Table ---
with st.expander("📋 Show Simulation Data"):
    st.dataframe(df.style.format({
        "Voting Weekly Fees": "%.2f",
        "Cumulative Voting Fees": "%.2f",
        "Relative Voting Earnings (%)": "%.2f",
        "Volume Weekly Rewards": "%.2f",
        "Cumulative Volume Rewards": "%.2f",
        "Baseline Volume Rewards (No Multiplier)": "%.2f",
        "Multiplier": "%.2f"
    }))
