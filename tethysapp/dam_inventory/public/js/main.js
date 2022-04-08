var isPlaying = false;
var options = JSON.parse(document.getElementById('options').textContent);
//#region Crear mapa
// var ol_map = new ol.Map({
//     controls: ol.control.defaults().extend([
//         new ol.control.FullScreen(),
//         new ol.control.ZoomSlider(),
//         new ol.control.Control({element: document.getElementById("controlsT")})
//       ]),
//     target: 'map',
//     layers: [
//       new ol.layer.Tile({
//         source: new ol.source.OSM()
//       })
//     ],
//     view: new ol.View({
//     center: [0, 0],
//       zoom: 2
//     })
// });


//#endregion
var app_actions = document.getElementById('app-actions');
var app_navigation = document.getElementById('app-navigation');
var app_content_wrapper = document.getElementById('app-content-wrapper');
app_actions.style.display = 'none';
app_navigation.style.display = 'none';


window.onload = function(){
    var ol_map = TETHYS_MAP_VIEW.getMap();

    var currentLayerControl = new ol.control.Control({element: document.getElementById("currentLayer")});

    var controlsT = new ol.control.Control({
        element: document.getElementById("controlsT")
    });
    ol_map.addControl(currentLayerControl);
    ol_map.addControl(controlsT);

    app_content_wrapper.classList.remove('show-nav');
    app_content_wrapper.classList.add('with-transition');

    //#region Añadir primera capa
        var newlayer = new ol.layer.Tile({
            source: new ol.source.TileWMS({
                url: 'http://localhost:8080/geoserver/wms',
                params: {'LAYERS': options[0][1]},
                serverType: 'geoserver'
            }),
        });
        ol_map.addLayer(newlayer);
    //#endregion
}

//#region Seleccionar capa
function selectLayer(layer) {
    var ol_map = TETHYS_MAP_VIEW.getMap();
    var labelLayer = document.getElementById("currentLayer");
    var layers = ol_map.getLayers();
    if (layers.getLength() > 1){
        ol_map.getLayers().item(1).getSource().updateParams({'LAYERS': layer});
        console.log('Layer setted to:' + layer);
    } else {
        var newlayer = new ol.layer.Tile({
            source: new ol.source.TileWMS({
                url: 'http://localhost:8080/geoserver/wms',
                params: {'LAYERS': layer},
                serverType: 'geoserver'
            }),
        });
        ol_map.addLayer(newlayer);
        console.log('Added layer:' + layer);
    }
    labelLayer.innerHTML = "Current Layer: "+layer;
    document.getElementById('selected-layer').textContent = layer;
}
//#endregion

//#region Avanzar capa
function nextLayer(){
    var currentLayer = document.getElementById("currentLayer").innerHTML.replace("Current Layer: ","");
    options.forEach(function(layer,index,array) {
        if (layer[1] == currentLayer){
            rangeInput.max = options.length-1;
            updaterange(index == options.length-1 ? 0 : index+1);
        }
    })
}
//#endregion

//#region Retroceder capa
function prevLayer(){
    var currentLayer = document.getElementById("currentLayer").innerHTML.replace("Current Layer: ","");
    options.forEach(function(layer,index,array) {
        if (layer[1] == currentLayer){
            rangeInput.max = options.length-1;
            updaterange(index == 0 ? options.length-1 : index-1);
        }
    })
}
//#endregion

//#region Auto-avanzar capas
function autoLayer(){
    isPlaying = true;
    play();    
}

async function play(){
    for (var i = 0; i < options.length; i++) {
        await new Promise(r => setTimeout(r, 1000));
        if (isPlaying){
            nextLayer();
        }
        else{
            break;
        }
    }
}
//#endregion

function pauseAutoLayer(){
    isPlaying = false;
}

//#region Slider function
let rangeInput = document.querySelector(".range-input input");
let rangeValue = document.querySelector(".range-input .value div");

let  start = parseFloat(rangeInput.min);
let end = parseFloat(rangeInput.max);
let step = parseFloat(rangeInput.step);

var length = options.length-1;

for(let i=start;i<=end;i+=step){
  rangeValue.innerHTML += '<div>'+i + " / " + length +'</div>';
}
rangeInput.addEventListener("input",function(){
    updaterange(this.value);
});

function updaterange(value){
  selectLayer(options[value][1]);
  rangeInput.value = value;
  let top = parseFloat(rangeInput.value)/step * -40;
  rangeValue.style.marginTop = top+"px";
}
//#endregion