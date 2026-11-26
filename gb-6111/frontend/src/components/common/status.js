import { EvidenceStates, States } from "../../constants/states.js";
import { el } from "../../utils/dom.js";

export function status(value) {
  return el("span", {class: `status state-${value}`, "data-state": value}, States[value] || value);
}

export function evidenceStatus(value) {
  const state = value === "invalidated" ? "invalidated" : "valid";
  return el("span", {class: `status evidence-${state}`, "data-evidence": state}, EvidenceStates[state]);
}
