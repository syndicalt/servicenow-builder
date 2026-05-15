# Sprint 142 Change Log

## Business Rule gate inference hardening

- Live demo story `STRY0010021` exposed that the deterministic Business Rule gate still required literal `Fields read:` and `Fields written:` labels.
- The gate now accepts equivalent story language when field reads are inferable from the condition and field writes are inferable from `set field ...`, `set ... to ...`, or `writes only ...` language.
- Negative safety constraints such as "must not use GlideRecord" and "not cross-table writes" are now stripped before forbidden-behavior detection when they are clearly prohibitions, not requested behavior.
- The deterministic validator remains fail-closed for generated scripts; this change only prevents clear, low-risk Business Rule stories from being routed to clarification because of wording style.
