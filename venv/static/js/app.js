function grafico1(){
    //Muestro el spinner
    document.getElementById('spinner-overlay').style.display='flex';

    //Llamo a la API
    fetch('infracciones?json=true')
    .then(response=> response.json())
    .then(data=>{
        if (data && data.grafico1){

            const grafico1=JSON.parse(data.grafico1);
            Plotly.newPlot('grafico1',grafico1.data,grafico1.layout,{responsive:true});
            document.getElementById('spinner-overlay').style.display='none';

        } else{
            console.error('Error: No se recibieron datos del grafico 1');
        }
    })
    .catch(error=>{
        console.error('Error al actualizar el grafico 1:',error)
        document.getElementById('spinner-overlay').style.display='none';
    });
}


function actualizarGraficos(){

    document.getElementById('spinner-overlay').style.display='flex';


        const fecha1 = document.getElementById('fecha1').value;
        const fecha2 = document.getElementById('fecha2').value;
        const errorMessage = document.getElementById('error-message');
        errorMessage.style.display = 'none';
        
        
        
        // Muestro el spinner
        
        fetch('/infracciones', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ fecha1, fecha2 })
    })
    .then(response => response.json())
    .then(data => {
        // Oculto el spinner
        document.getElementById('spinner-overlay').style.display = 'none';
        
        if(data && data.grafico2){
            const grafico2=JSON.parse(data.grafico2);
            Plotly.newPlot('grafico2',grafico2.data,{
                ...grafico2.layout,
                responsive: true,
                margin: {t:40,l:20,r:20,b:80},
                hoverlabel:{bgcolor: 'white',font:{size:14}},
                legend: {
                    x:0.1,
                    xanchor:0.6,
                    yanchor:'top'
                }
            });
        } else {
            errorMessage.textContent += '\nError: No se recibieron datos del gráfico 2.';
            errorMessage.style.display = 'block';
        }

        if(data && data.grafico3){
            const grafico3=JSON.parse(data.grafico3);
            Plotly.newPlot('grafico3', grafico3.data, grafico3.layout, { responsive: true });
            
        } else{
            errorMessage.textContent+= '\n Error: No se recibieron datos del grafico 3.';
            errorMessage.style.display = 'block';
        }
    })
    .catch(error => {
        // Oculto el spinner en caso de error
        document.getElementById('spinner-overlay').style.display = 'none';
        errorMessage.textContent = `Error al cargar el gráfico: ${error}`;
        errorMessage.style.display = 'block';
    });
};

//Actualizacion del grafico 1
document.addEventListener('DOMContentLoaded',()=>{
    grafico1();
});

setInterval(grafico1,300000);

//Actualizacion inicial al cargar la pagina o enviar el formulario
document.getElementById('form1').addEventListener('submit',function(event){
    event.preventDefault();
    actualizarGraficos();
});

//Actualizacion cada 5 minutos (300000 ms)
setInterval(actualizarGraficos,300000);