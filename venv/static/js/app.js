document.getElementById('form1').addEventListener('submit', function(event) {
    event.preventDefault();

    const fecha1 = document.getElementById('fecha1').value;
    const fecha2 = document.getElementById('fecha2').value;
    const errorMessage = document.getElementById('error-message');
    errorMessage.style.display = 'none';

    // Muestro el spinner
    document.getElementById('spinner-overlay').style.display = 'flex';

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
        if (data && data.grafico1) {
            const grafico1 = JSON.parse(data.grafico1);
            Plotly.newPlot('grafico1', grafico1.data, grafico1.layout, { responsive: true });
        } else {
            errorMessage.textContent = 'Error: No se recibieron datos del gráfico.';
            errorMessage.style.display = 'block';
        }

        if(data && data.grafico2){
            const grafico2=JSON.parse(data.grafico2);
            Plotly.newPlot('grafico2',grafico2.data,{
                ...grafico2.layout,
                responsive:true,
                margin: {t:40,l:20,r:20,b:80},
                hoverlabel:{bgcolor: 'white',font:{size:14}}
        });
        } else{
            errorMessage.textContent+='\nError: No se recibieron datos'
            errorMessage.style.display='block'
        }
    })
    .catch(error => {
        // Oculto el spinner en caso de error
        document.getElementById('spinner-overlay').style.display = 'none';
        errorMessage.textContent = `Error al cargar el gráfico: ${error}`;
        errorMessage.style.display = 'block';
    });
});