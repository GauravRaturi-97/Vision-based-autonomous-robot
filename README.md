# 🤖 AURA-Bot: Autonomous Voice-Commanded Industrial Inspection & Pedestrian-Tracking Robot
> **Hack in Hills '26 — Powered by TinyFish & Render Workflows**

[![YOLO11s mAP50](https://img.shields.io/badge/YOLO11s_mAP50-99.5%25-brightgreen)](#benchmark-results)
[![Multi-World Success](https://img.shields.io/badge/120--Trial_Benchmark-99.2%25_Success-blue)](#benchmark-results)
[![TinyFish MCP](https://img.shields.io/badge/Sponsor-TinyFish_MCP_Integrated-orange)](#tinyfish--render-workflows-integration)
[![Render Workflows](https://img.shields.io/badge/Sponsor-Render_Workflows_SDK-purple)](#tinyfish--render-workflows-integration)

---

## 📌 1. Problem Statement
Industrial warehouses, factories, and break-room facilities suffer from two critical bottlenecks:
1. **Static Automation Blindness:** Traditional AGVs follow fixed magnetic tape on the floor—they cannot dynamically locate moving human workers, understand natural voice orders, or adapt to unmapped clutter.
2. **Disconnected Safety & Compliance Intelligence:** Physical robots cannot access live web regulations (OSHA hazmat rules, equipment recalls, live dispatch tickets) when inspecting hazardous assets like gas canisters, oil barrels, or forklifts.

**AURA-Bot** bridges **Embodied Physical AI** (YOLO11s Computer Vision + 2D LiDAR + Local Ollama LLM) with **Live Cloud Web Intelligence** (**TinyFish MCP** + **Render Workflows**).

---

## 🏗️ 2. System Architecture & Workflow Diagram

```mermaid
flowchart TD
    subgraph Operator["🎙️ Human Operator"]
        V["Voice / Natural Language Order<br/>e.g. 'Go to the oil barrel and then go to the pedestrian'"]
    end

    subgraph EdgeBrain["🧠 Onboard Edge Brain (Jetson Orin Nano / Webots Controller)"]
        STT["sounddevice + SpeechRecognition"]
        NLU["Two-Stage Intent Engine<br/>0.001s Reflex NLU + Local Ollama (llama3.2:1b)"]
        QUEUE["Multi-Step Mission Queue"]
        YOLO["Custom YOLO11s Pedestrian Detector<br/>(mAP50: 0.995 | Precision: 0.999)"]
        LIDAR["360° 2D LiDAR FSM<br/>(Wall-Lock, Stagnation Breaker, Escape)"]
        SCAN["Zero-Config Scene-Tree Landmark Scanner<br/>(46+ Dynamic Targets)"]
    end

    subgraph CloudSponsors["☁️ Cloud Intelligence & Durable Workflows"]
        RW["Render Workflows (@app.task)<br/>Parallel Fan-Out via asyncio.gather()"]
        TF["🐟 TinyFish MCP & Search Toolkit<br/>(mcp__tinyfish__search & /v1/automation/run)"]
        LOG["Durable JSON Compliance Audit<br/>(render_tinyfish_audit_log.json)"]
    end

    V --> STT --> NLU --> QUEUE
    SCAN --> NLU
    QUEUE --> YOLO & LIDAR
    YOLO & LIDAR -->|Arrived at Asset / Worker| RW
    RW -->|Task 1: Web OSHA Lookup| TF
    RW -->|Task 2: LiDAR Clearance Audit| LOG
    TF --> LOG
Gaurav Raturi and Yogesh Gautam, Gurugram University
