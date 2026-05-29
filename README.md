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

浏览器打开 → 下载PNG（2x，适合学术论文插图）：

| 图号 | 文件 | 内容 |
|------|------|------|
| 图6 | `figures/图6-缺陷密度标度律实验.html` | 散点图+幂律拟合曲线（α=0.179, p<0.01） |
| 图7 | `figures/图7-形式化缺陷天花板效应.html` | 验证前后安全属性通过率对比（+47%增益） |
| 图8 | `figures/图8-多LLM缺陷标度对比.html` | GPT-4/DeepSeek-Coder/Qwen跨模型标度律对比 |
| 图9 | `figures/图9-误差链累积与密集验证断链.html` | 自回归误差链累积机制与密集验证断链效应（BES Theorem 4.4a/4.5） |
| 图10 | `figures/图10-组合式vs单体缺陷密度对比.html` | 组合式正确性 vs 单体生成的指数级优势 |
| 图11 | `figures/图11-验证复杂度标度律.html` | Z3/NuSMV求解时间 vs LOC和属性数量的标度律 |
| 图12 | `figures/图12-研究框架全景图.html` | 科学问题→研究内容→创新点三层框架全景 |
| 图13 | `figures/图13-实验设计概览.html` | 3场景×4规模×验证管道的实验设计总览 |

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
