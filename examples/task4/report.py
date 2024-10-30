import pandas as pd

df = pd.read_csv("brench.csv")

all_numbers = pd.to_numeric(df['result'], errors='coerce').notnull().all()
if not all_numbers:
    raise ValueError("The 'result' column should contain only numbers.")

improvements = {}
for benchmark in df['benchmark'].unique():
    benchmark_data = df[df['benchmark'] == benchmark]
    result_remove_nops = benchmark_data[benchmark_data['run'] == 'remove_nops']['result'].values[0]
    result_alias_analysis = benchmark_data[benchmark_data['run'] == 'alias_analysis']['result'].values[0]
    improvement = result_remove_nops - result_alias_analysis
    improvements[benchmark] = improvement/result_remove_nops

max_improvement = max(improvements.values())
min_improvement = min(improvements.values())
avg_improvement = sum(improvements.values()) / len(improvements)

for benchmark, improvement in improvements.items():
    print(f"{benchmark}: {improvement}")

print(f"Maximum Improvement: {max_improvement}")
print(f"Minimum Improvement: {min_improvement}")
print(f"Average Improvement: {avg_improvement}")
