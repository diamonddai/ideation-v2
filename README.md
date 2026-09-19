# MetaMuse

An LLM-based multi-agent system for ideating **metaphorical visualizations**.

In data visualization, metaphor maps abstract data—the *tenor*—onto familiar visuospatial phenomena—the *vehicle*. The two are linked by the *ground*: shared attributes that make the mapping intelligible. Effective metaphorical designs can capture attention, improve memorability, and evoke emotional resonance. Ideating them is still hard. Designers must generate diverse candidate vehicles while remaining creative enough to surprise an audience, and both goals depend on interdisciplinary knowledge.

Prior support has followed two paths. Theoretical frameworks, such as Ha et al.'s taxonomy of metaphorical visualization, mainly help analyze existing designs after the fact rather than invent new vehicles. Retrieval systems such as MetaGlyph can quickly surface metaphorical imagery from existing libraries, but they are bound to those repositories and rarely produce creative candidates.

LLM-based multi-agent systems suggest another route. Role specialization and heterogeneous models can increase diversity; collaboration and refinement can go beyond the patterns of a single model. **MetaMuse** follows this approach. Given a dataset, it identifies the data theme as the tenor and generates diverse, creative vehicle candidates so designers can ideate more broadly.

The system is grounded in formative interviews with six domain experts and a design space built from 60 exemplary metaphorical visualizations along semantic, functional, perceptual, and structural dimensions. On top of that space, MetaMuse uses a bio-inspired dual-channel framework:

- **Guided** — structured exploration of the design space, aimed at diversity
- **Blind** — stochastic variation, aimed at creativity

In the convergent phase, designers can adjust tenor–vehicle mappings and generate visualization previews for fast prototyping. A controlled experiment, example gallery, user study, and expert interviews indicate that MetaMuse helps both novice and expert designers ideate diverse and creative metaphorical visualizations.

## Contributions

- A corpus of 60 high-quality metaphorical visualizations, and a design space of how grounds link tenors to vehicles
- A bio-inspired multi-agent framework with Guided (structured) and Blind (free) divergence channels
- The MetaMuse system, covering the full ideation workflow: data understanding, vehicle divergence, and convergence with interactive mapping and preview

## Workflow

1. **Understand** — identify the data theme (tenor) from a tabular dataset
2. **Diverge** — generate vehicle candidates through the Guided and Blind channels
3. **Converge** — refine tenor–vehicle mappings and preview visualizations

```
metaphor_backend/    FastAPI multi-agent backend
metaphor_frontend/   React + TypeScript + Vite interface
```

## Quick start

**Backend**

```bash
cd metaphor_backend
cp .env.example .env   # fill in your API keys; do not commit .env
pip install -r requirements.txt
python main.py
```

API docs: `http://localhost:8000/docs`

**Frontend**

```bash
cd metaphor_frontend
npm install
npm run dev
```

See `metaphor_backend/README.md` and `metaphor_frontend/README.md` for module-level details.
