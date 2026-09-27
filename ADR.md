# ADR: Late Payment Fee Policy

## Decision

Late payment fee must be 1.5% of outstanding balance per finance policy FIN-2024-03.

## Context

The fee service owns fee calculations so payment processing uses one shared
policy boundary. The toy implementation keeps calculations local and
deterministic for the demo.