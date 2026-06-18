import pandas as pd

# Read the results
df = pd.read_csv("results.csv")

# Group by model and calculate statistics
print("=" * 80)
print("BENCHMARK RESULTS SUMMARY")
print("=" * 80)

for model in df["model"].unique():
    model_data = df[df["model"] == model]

    # Filter out errors
    successful = model_data[model_data["error"].isna() | (model_data["error"] == "")]

    if len(successful) == 0:
        print(f"\n❌ {model}: NO SUCCESSFUL RUNS")
        print(
            f"   Errors: {model_data['error'].iloc[0] if len(model_data) > 0 else 'Unknown'}"
        )
        continue

    avg_latency = successful["latency_s"].mean()
    min_latency = successful["latency_s"].min()
    max_latency = successful["latency_s"].max()
    parse_success_rate = (successful["parse_ok"].sum() / len(successful)) * 100
    avg_suggestions = successful["suggestions_count"].mean()

    print(f"\n✅ {model.upper()}")
    print(f"   {'─'*60}")
    print(f"   Avg Latency:      {avg_latency:.2f}s")
    print(f"   Min Latency:      {min_latency:.2f}s")
    print(f"   Max Latency:      {max_latency:.2f}s")
    print(f"   Parse Success:    {parse_success_rate:.1f}%")
    print(f"   Avg Suggestions:  {avg_suggestions:.1f}")
    print(f"   Total Runs:       {len(successful)}/{len(model_data)}")

print("\n" + "=" * 80)
print("RECOMMENDATION")
print("=" * 80)

# Find best model by latency
successful_models = (
    df[df["error"].isna() | (df["error"] == "")]
    .groupby("model")["latency_s"]
    .mean()
    .sort_values()
)

if len(successful_models) > 0:
    fastest = successful_models.index[0]
    fastest_time = successful_models.iloc[0]

    print(f"\n🏆 FASTEST MODEL: {fastest.upper()}")
    print(f"   Average Response Time: {fastest_time:.2f}s")
    print(f"\n   This is the best choice for real-time feedback analysis!")
else:
    print("\nNo successful runs to compare.")

print("\n" + "=" * 80)
