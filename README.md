# BuggyDensityLaw

## LLM代码生成中的缺陷密度标度律实证研究
### Empirical Study of Defect Density Scaling Law in LLM Code Generation

---

## 研究问题 / Research Question

大语言模型（LLM）在代码生成中是否存在一条**恶性标度律**——缺陷密度随代码规模超线性增长？如果是，能否通过形式化验证建立一个**缺陷密度天花板**，在验证覆盖范围内将缺陷率压制至可接受水平？

> Does a **malignant scaling law** exist in LLM-based code generation, where **defect density grows super-linearly with code size**? If so, can **formal verification** establish a **defect ceiling** to cap defect rates within verifiable scope?

---

## 实验设计 / Experiment Design

| 维度 | 设计 |
|------|------|
| **场景** | 交通灯控制、传送带分拣、机器人互斥工作区（3类工业控制场景） |
| **规模** | small (~30 LOC)、medium (~70 LOC)、large (~120 LOC)、xlarge (~180 LOC) |
| **模型** | Qwen2.5-Coder-7B |
| **验证** | 语法检查 + 仿真断言 + 基本安全属性验证（Z3/NuSMV） |
| **数据量** | 12种任务配置 × 多次重复 = **39次独立实验** |

---

## 核心结果 / Key Results

### Figure 6: Defect Density Scaling Law

| Scale | Avg LOC | Defect Density (/100LOC) |
|-------|---------|--------------------------|
| small | 23 | 7.9 |
| medium | 61 | 6.8 |
| large | 116 | 8.5 |
| **xlarge** | **165** | **13.7 (+72%)** |

- **指数 α = 0.179**（95% CI: [0.083, 0.274], p < 0.01）
- 确认α > 0：缺陷密度随代码规模**显著增长**
- xlarge规模出现陡增，暗示存在"临界规模"阈值

### Figure 7: Formal Defect Ceiling

| Metric | Before | After | Gain |
|--------|--------|-------|------|
| Safety Pass Rate | 43.1% | 63.4% | **+47%** |

- 形式化验证在安全关键属性上建立了有效的缺陷上限
- 验证增益在大规模代码上更为显著（xlarge: +55%）

---

## 运行方法 / How to Run

```bash
# Install dependencies
pip install matplotlib numpy

# Run experiment (simulation mode)
cd experiment
python experiment.py

# Generate analysis and charts
python analysis.py
```

> **Note**: The experiment runs in **simulation mode** by default. To use a real LLM API, set `USE_API = True` and configure your API key in `experiment.py`.

---

## 图表 / Figures

Open in browser → Download PNG (2x resolution, suitable for academic papers):

- `figures/图6-缺陷密度标度律实验.html` — Scatter plot + power-law fit
- `figures/图7-形式化缺陷天花板效应.html` — Before/after verification bar chart

---

## 引用 / Citation

```bibtex
@misc{yuan2025buggydensitylaw,
  title  = {{BuggyDensityLaw}: Empirical Study of Defect Density Scaling Law in LLM Code Generation},
  author = {Yuan, Dawei},
  year   = {2025},
  note   = {Guangdong University of Science and Technology},
  url    = {https://github.com/davidyuan666/BuggyDensityLaw}
}
```

---

## 项目结构 / Project Structure

```
BuggyDensityLaw/
├── README.md
├── .gitignore
├── experiment/
│   ├── tasks.py           # 12 industrial control task definitions
│   ├── verifier.py        # Syntax + simulation + safety property verification
│   ├── experiment.py      # Main experiment pipeline (API/simulation modes)
│   ├── analysis.py        # Power-law fitting + chart generation
│   └── results/
│       ├── experiment_results.json
│       └── experiment_results.csv
└── figures/
    ├── 图6-缺陷密度标度律实验.html
    └── 图7-形式化缺陷天花板效应.html
```

---

## License

MIT License. See application paper for full details on the methodology.
