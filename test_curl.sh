#!/bin/bash
echo -e "\n### Testing TEXT input ###"
curl -s -X POST http://localhost:8000/voice/voice_chat \
  -H "Content-Type: application/json" \
  -d '{"text":"hello test"}' | jq .

echo -e "\n\n### Testing ERROR input (Empty Body) ###"
curl -s -X POST http://localhost:8000/voice/voice_chat \
  -H "Content-Type: application/json" \
  -d '{}' | jq .

echo -e "\n\n### Testing ERROR input (No Body) ###"
curl -s -X POST http://localhost:8000/voice/voice_chat | jq .
