import { io } from "socket.io-client";

const COMM_TYPES = {
  JUPYTER: 'JUPYTER',
  COLAB: 'COLAB',
  CUSTOM_WS_API: 'CUSTOM_WS_API',
};

export default class CommAPI {
  constructor(api_call_id, callback) {
    this.callback = callback;
    this.mode = null;
    if (window.Jupyter !== undefined) {
      this.mode = COMM_TYPES.JUPYTER;
      this.comm = window.Jupyter.notebook.kernel.comm_manager.new_comm(
        api_call_id,
        {}
      );
      this.comm.on_msg(msg => {
        const data = msg.content.data;
        callback(data);
      });
    } else if (window.google !== undefined) {
      this.mode = COMM_TYPES.COLAB;
      this.comm = async function (msg) {
        const result = await google.colab.kernel.invokeFunction(
          api_call_id,
          [msg], // The argument
          {}
        ); // kwargs
        callback(result.data['application/json']);
      };
    } else {
      console.log('Cannot find Jupyter/Colab namespace.');
      console.log('Trying to connect to custom web socket API...');
      this.connect(api_call_id);
    }
  }

  connect(api_call_id) {
    var socket = io();
    socket.on('connect', () => {
        console.log("Connected to custom WebSocket API.");
        this.mode = COMM_TYPES.CUSTOM_WS_API;
        this.comm = (msg) => {
          console.log('Sending WS message: ', api_call_id, msg);
          socket.emit(api_call_id, msg, (response) => {
            console.log(api_call_id + ' response:', response); // ok
            this.callback(response);
          });
        }
    });
  }

  call(msg) {
    if (this.comm) {
      if (this.mode === COMM_TYPES.JUPYTER) {
        this.comm.send(msg);
      } else if (this.mode === COMM_TYPES.COLAB) {
        this.comm(msg);
      } else if (this.mode === COMM_TYPES.CUSTOM_WS_API) {
        this.comm(msg);
      } else {
        throw Error('Invalid state: kernel connection not initialized.')
      }
    }
  }
}
