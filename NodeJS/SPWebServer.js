const express = require('express')
const mysql = require('mysql')
const app = express()
const port = 3000;
const bodyParser = require('body-parser');
var mqtt = require('mqtt');
var client = mqtt.connect('mqtt://127.0.0.1:1883');


// app.use(express.urlencoded({ extended: false}));
app.use(express.json());
app.set('view engine', 'ejs');
app.use('/assets', express.static('assets'));
app.use(bodyParser.json())
app.use(bodyParser.urlencoded({extended: false}))


/*
! get connection to our DB
*/
function getConnection(){
  return mysql.createConnection({
    multipleStatements: true,
    host: 'localhost',
    port: '3306',
    user: 'root',
    password: '123321',
    database: 'kitchenguard'
  });
}

/*
! connect to mqtt
*/
client.on('connect', function () {
  client.subscribe('server', function (err) {
    if (!err) {
      console.log("Connected to mqtt.")
    }
  })
})


/*
! GET METHODS.
*/

app.get('/', (req, res) => {

  queryString = "SELECT * FROM kitchenguard";   // SQL query to get all content from kitchenguard table

  getConnection().query(queryString, (err, rows, fields) => {
    if (err){
      console.log(err);
    }
  res.render('table', { title: 'User List', userData: rows})
  })
})

/*
! mqtt subscibes to topics of "/server"
*/
client.on('message', function (topic, message) {
    console.log(message.toString())
    msg = JSON.parse(message.toString())
    console.log(msg.startTime, msg.endTime)

    queryString = "INSERT INTO kitchenguard (start, stop, frq, time_total) VALUES (?, ?, ?, ?)"; // SQL query to insert data to kitchenguard table

    getConnection().query(queryString, [msg.startTime, msg.endTime, msg.value, msg.value2], (err, results, fields) =>{
      if (err){
        console.log(err);
      }
      //res.status(200).send('success 1')
  })
  client.end()
})

/*
! app listen
 */

app.listen(port, () => console.log(`app listening on port ${port}!`));







