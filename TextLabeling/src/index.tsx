import React from 'react';
import ReactDOM from 'react-dom';
import {select} from 'd3-selection';
import 'regenerator-runtime/runtime';
import {DataSample, TextSample} from './types';
import { TextAnalyzer } from './TextAnalyzer';

export function renderProfilerViewBundle(divName: Element, data: TextSample) {
  ReactDOM.render(<TextAnalyzer hit={data} />, select(divName).node());
}
