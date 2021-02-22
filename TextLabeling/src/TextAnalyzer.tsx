import * as React from 'react';
import { DataSample, TextSample } from './types';
import { WordEntityBarCharts } from './WordEntityBarCharts';
import { useTable, Column, ColumnInstance, HeaderGroup } from 'react-table';
import { useState } from 'react';
import CommAPI from './CommAPI';
import { VegaLite } from 'react-vega';
import { TopLevelSpec as VlSpec } from 'vega-lite';

interface TableProps {
    columns: Array<Column<string[]>>;
    data: string[][];
    hit: TextSample;
    setLabel: (label: string, id: number) => void;
}

// Compact and Detail view share the same body content. Just the header will change.
function TableCompactDetailView(props: {
    columns: Array<Column<string[]>>;
    data: string[][];
    headerGroups: Array<HeaderGroup<string[]>>;
    hit: TextSample;
    setLabel: (label: string, id: number) => void;
  }) {
    const { columns,data, hit } = props;
    const { getTableBodyProps, headerGroups, rows, prepareRow } = useTable({
      columns,
      data,
    });
    // let [labelColorPos, setLabelColorPositive] = useState("gray");
    return (
      <>
        <thead>
          {headerGroups.map((headerGroup, i) => (
            <tr {...headerGroup.getHeaderGroupProps()}>
              {headerGroup.headers.map((column, i) => (
                <th
                  scope="col"
                  {...column.getHeaderProps()}
                  style={{
                    position: 'sticky',
                    top: '-1px',
                    background: '#eee',
                    zIndex: 1,
                    width:200,
                    textAlign: 'left',
                  }}
                >
                  {column.render('Header')}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody {...getTableBodyProps()}>
        {
        props.hit.samples.map((row, i) => {
            let labelColorPos = row.label === 'positive'
            ? "dodgerblue"
            : "gray";
            let labelColorNeg = row.label === 'negative'
            ? "#f44336"
            : "gray";

            return (
            <tr key={'column' + i} >
                <td style={{textAlign: 'left'}}>
                {row.text}
                </td>
                <td style={{textAlign: 'left'}}>
                <button
                      type="button"
                      title={"Positive Label"}
                      className="btn btn-gray btn-sm  active"
                      style={{ padding: '3px', backgroundColor: labelColorPos}}
                      onClick={() => props.setLabel("positive", i)}
                    >
                      Positive
                    </button>
                    <button
                      type="button"
                      title={"Negative Label"}
                      className="btn btn-gray btn-sm  active"
                      style={{ padding: '3px', backgroundColor: labelColorNeg}}
                      onClick={() => props.setLabel("negative", i)}
                    >
                      Negative
                    </button>

                </td>
            </tr>
            );
        })
        }
        </tbody>
      </>
    );
  }

function Table(props: TableProps) {
    const { columns, data, hit } = props;
    const { getTableProps, headerGroups } = useTable({
      columns,
      data,
    });
    return (
      <table {...getTableProps()} className="table table-hover small">
        <TableCompactDetailView columns={columns} data={data} headerGroups={headerGroups}  hit={hit} setLabel={(label:string, id: number) => props.setLabel(label, id)}/>
      </table>
    );
  }

  
interface TextAnalyzerState {
    data: TextSample;
}
interface TextAnalyzergProps {
    hit: TextSample;
    // handleDialogExecution: (selectedOperator: AppliedOperator) => void;
}

class TextAnalyzer extends React.PureComponent <TextAnalyzergProps, TextAnalyzerState> {
    commGetCandidates: CommAPI;
    constructor(props: TextAnalyzergProps) {
        super(props);
        this.state = { data: this.props.hit };
        // this.handleChangeNewColumnName = this.handleChangeNewColumnName.bind(this);
        this.commGetCandidates = new CommAPI(
            'get_candidates_comm_api',
            (msg: {candidates: TextSample}) => {
              this.setState({data: msg['candidates']});
            }
          );
    }
    // handleChangeNewColumnName(event: React.ChangeEvent<HTMLInputElement>) {
    //   const columnName = event.target.value;
    //   this.setState({selectedOperator: {...this.state.selectedOperator, newColumnName: columnName}});
    // };
    setLabel (label: string, id: number){
        let datatemp = this.state.data.samples
        datatemp[id].label = label
        this.setState({data: {...this.state.data, samples:datatemp}})
    }
    getCandidates() {
        this.commGetCandidates.call({labeled_data: this.state.data.samples});
    }
    getSpecification(): VlSpec {
        const specification = {
          width: '120',
          height: '120',
          title: "F1 during the Active Learning",
          data: { name: 'values' },
          description: 'A simple bar chart with embedded data.',
          encoding: {
            x: { field: 'Iterations', type: 'ordinal' },
            y: { field: 'F1', type: 'quantitative' },
            tooltip: [
                { field: 'Iterations', title: 'Iterations', type: 'quantitative' },
                { field: 'F1', title: 'F1', type: 'quantitative' },
            ],
          },
          mark: 'bar',
        };
        return specification as VlSpec;
      }
    render(){
        const headers = ["Text", 'Label']
        const rows = [["1", "2"]];
    
        const columns = headers.map((h, i) => ({
          Header: h,
          accessor: (row: string[]) => row[i],
        }));
        
        let performanceData: any = []
        this.state.data.performance_history.map((performance, idx) => 
            performanceData.push({'Iterations': idx*5, 'F1': performance.toFixed(2)}))

        const barData = {
            values: performanceData,
          }
        return (
            <div>
                <div style={{textAlign: 'center', margin: 15}}>
                    <h3>Guided Labeling using Active Learming</h3>
                </div>
                {/* <div>
                    Performance history:
                    {
                    this.state.data.performance_history.map(performance =>
                        <span>{performance.toFixed(2)}</span>)
                    }
                </div> */}
                <VegaLite
                    spec={this.getSpecification()}
                    data={barData}
                />
                <div>
                    <button
                        type="button"
                        title={"Update Model"}
                        className="btn btn-gray btn-sm active"
                        style={{ padding: '3px'}}
                        onClick={() => this.getCandidates()}
                    >
                        Update Model
                    </button>
                </div>
            <div className="mt-2">
            <Table
              columns={columns}
              data={rows}
              hit={this.state.data}
              setLabel={(label:string, id: number) => this.setLabel(label, id)}
            />
          </div>
            {/* <WordEntityBarCharts hit={hit} /> */}
        </div>
        )
    }
}

export {TextAnalyzer};