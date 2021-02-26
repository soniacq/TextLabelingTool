import * as React from 'react';
import {DataSample, TextSample} from './types';
import {WordEntityBarCharts} from './WordEntityBarCharts';
import {useTable, Column, ColumnInstance, HeaderGroup} from 'react-table';
import {useState} from 'react';
import CommAPI from './CommAPI';
import {VegaLite} from 'react-vega';
import {TopLevelSpec as VlSpec} from 'vega-lite';
import Button from '@material-ui/core/Button';
import {makeStyles} from '@material-ui/core/styles';
import MauTable from '@material-ui/core/Table';
import TableBody from '@material-ui/core/TableBody';
import TableCell from '@material-ui/core/TableCell';
import TableContainer from '@material-ui/core/TableContainer';
import TableHead from '@material-ui/core/TableHead';
import TableRow from '@material-ui/core/TableRow';
import Paper from '@material-ui/core/Paper';
import './TextAnalyzer.css';

const useStyles = makeStyles({
  table: {
    minWidth: '200px',
    fontWeight: 600,
    textAlign: 'left !important' as 'left',
  },
});

interface TableProps {
  columns: Array<Column<string[]>>;
  data: string[][];
  hit: TextSample;
  setLabel: (label: string, id: number) => void;
}

function Table(props: TableProps) {
  const {columns, data, hit} = props;
  const {
    getTableProps,
    getTableBodyProps,
    headerGroups,
    rows,
    prepareRow,
  } = useTable({
    columns,
    data,
  });
  const classes = useStyles();
  return (
    <TableContainer component={Paper}>
      <MauTable {...getTableProps()}>
        <TableHead>
          {headerGroups.map((headerGroup, i) => (
            <TableRow {...headerGroup.getHeaderGroupProps()}>
              {headerGroup.headers.map((column, i) => (
                <TableCell
                  {...column.getHeaderProps()}
                  className={classes.table}
                >
                  {column.render('Header')}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableHead>
        <TableBody {...getTableBodyProps()}>
          {props.hit.samples.map((row, i) => {
            let labelColorPos =
              row.label === 'positive' ? 'dodgerblue' : 'gray';
            let labelColorNeg = row.label === 'negative' ? '#f44336' : 'gray';
            return (
              <TableRow key={'column' + i}>
                <TableCell style={{textAlign: 'left'}}>{row.text}</TableCell>
                <TableCell
                  style={{textAlign: 'left'}}
                  className={classes.table}
                >
                  <Button
                    variant="contained"
                    title={'Positive Label'}
                    style={{backgroundColor: labelColorPos}}
                    onClick={() => props.setLabel('positive', i)}
                  >
                    Positive
                  </Button>
                  <Button
                    variant="contained"
                    title={'Negative Label'}
                    style={{marginLeft: '3px', backgroundColor: labelColorNeg}}
                    onClick={() => props.setLabel('negative', i)}
                  >
                    Negative
                  </Button>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </MauTable>
    </TableContainer>
  );
}

interface TextAnalyzerState {
  data: TextSample;
}

interface TextAnalyzerProps {
  hit: TextSample;
}

class TextAnalyzer extends React.PureComponent<
  TextAnalyzerProps,
  TextAnalyzerState
> {
  commGetCandidates: CommAPI;
  constructor(props: TextAnalyzerProps) {
    super(props);
    this.state = {data: this.props.hit};
    this.commGetCandidates = new CommAPI(
      'get_candidates_comm_api',
      (msg: {candidates: TextSample}) => {
        this.setState({data: msg['candidates']});
      }
    );
  }

  setLabel(label: string, id: number) {
    const datatemp = this.state.data.samples;
    datatemp[id].label = label;
    this.setState({data: {...this.state.data, samples: datatemp}});
  }

  getCandidates() {
    this.commGetCandidates.call({labeled_data: this.state.data.samples});
  }

  getSpecification(): VlSpec {
    const specification = {
      width: '120',
      height: '120',
      title: 'F1 during the Active Learning',
      data: {name: 'values'},
      description: 'A simple bar chart with embedded data.',
      encoding: {
        x: {field: 'Iterations', type: 'ordinal'},
        y: {field: 'F1', type: 'quantitative'},
        tooltip: [
          {field: 'Iterations', title: 'Iterations', type: 'quantitative'},
          {field: 'F1', title: 'F1', type: 'quantitative'},
        ],
      },
      mark: 'bar',
    };
    return specification as VlSpec;
  }

  render() {
    const headers = ['Text', 'Label'];
    const rows = [['1', '2']];

    const columns = headers.map((h, i) => ({
      Header: h,
      accessor: (row: string[]) => row[i],
    }));

    let performanceData: any = [];
    this.state.data.performance_history.map((performance, idx) =>
      performanceData.push({Iterations: idx * 5, F1: performance.toFixed(2)})
    );

    const barData = {
      values: performanceData,
    };
    return (
      <div className="text-labeling">
        <div style={{textAlign: 'center', margin: 15}}>
          <h3>Guided Labeling using Active Learning</h3>
        </div>
        {/* <div>
                Performance history:
                {
                this.state.data.performance_history.map(performance =>
                    <span>{performance.toFixed(2)}</span>)
                }
            </div> */}
        <div style={{height: 200}}>
          <VegaLite spec={this.getSpecification()} data={barData} />
        </div>
        <div>
          <Button
            color="primary"
            variant="contained"
            onClick={() => this.getCandidates()}
          >
            Update Model
          </Button>
        </div>
        <div style={{marginTop: 6}}>
          <Table
            columns={columns}
            data={rows}
            hit={this.state.data}
            setLabel={(label: string, id: number) => this.setLabel(label, id)}
          />
        </div>
      </div>
    );
  }
}

export {TextAnalyzer};
