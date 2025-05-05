// Función para crear el dropdown con checkboxes de tipos de infracción
function crearCheckboxes(tipos, filtrosPrevios = null) {
    const contenedor = document.getElementById("dropdownTiposContainer");
    const dropdownBtn = document.getElementById("dropdownTipos");
    contenedor.innerHTML = "";
  
    // Crear checkbox "TODAS"
    const liTodas = document.createElement("li");
    liTodas.innerHTML = `
      <div class="form-check">
        <input type="checkbox" id="checkTodas" class="form-check-input" value="TODAS" checked>
        <label for="checkTodas" class="form-check-label">TODAS</label>
      </div>`;
    contenedor.appendChild(liTodas);
  
    // Agregar divisor
    const hr = document.createElement("hr");
    hr.classList.add("dropdown", "divider");
    contenedor.appendChild(hr);
  
    // Agregar cada tipo de infracción como checkbox
    tipos.forEach((tipo, index) => {
      const li = document.createElement("li");
      const isSelected = filtrosPrevios && filtrosPrevios.includes(tipo);
      li.innerHTML = `
        <div class="form-check">
          <input type="checkbox" id="checkTipo${index}" class="form-check-input checkTipo" value="${tipo}" ${isSelected ? "checked" : ""}>
          <label for="checkTipo${index}" class="form-check-label">${tipo}</label>
        </div>`;
      contenedor.appendChild(li);
    });
  
    // Asignar evento al checkbox "TODAS"
    const checkTodas = document.getElementById("checkTodas");
    if (checkTodas) {
      checkTodas.addEventListener("change", function () {
        if (this.checked) {
          document.querySelectorAll(".checkTipo").forEach(c => (c.checked = false));
        }
        actualizarTextoDropdown();
      });
    }
  
    // Asignar evento a cada checkbox individual
    document.querySelectorAll(".checkTipo").forEach(check => {
      check.addEventListener("change", function () {
        const todas = document.getElementById("checkTodas");
        if (todas) {
          todas.checked = false;
        }
        actualizarTextoDropdown();
      });
    });
  
    // Función para actualizar el texto del botón del dropdown
    function actualizarTextoDropdown() {
      const checkTodas = document.getElementById("checkTodas");
      const seleccionadas = [...document.querySelectorAll(".checkTipo:checked")].map(c => c.value);
  
      if (checkTodas && checkTodas.checked || seleccionadas.length === 0) {
        dropdownBtn.textContent = "Todas las infracciones";
      } else if (seleccionadas.length === 1) {
        dropdownBtn.textContent = seleccionadas[0];
      } else {
        dropdownBtn.textContent = `${seleccionadas.length} seleccionadas`;
      }
    }
  
    actualizarTextoDropdown();
  }
  
  // Función para obtener los tipos seleccionados; si "TODAS" está marcada, devuelve null
  function getTiposSeleccionados() {
    const checkTodas = document.getElementById("checkTodas");
    if (!checkTodas) return null;
    if (checkTodas.checked) return null; // null implica "TODAS"
    
    const seleccionados = [];
    document.querySelectorAll(".checkTipo:checked").forEach(check => {
      seleccionados.push(check.value);
    });
    return seleccionados;
  }
  
  // Función para actualizar el mapa
  function actualizarMapa() {
    document.getElementById("spinner-overlay").style.display = "flex";
  
    const fecha1 = document.getElementById("fecha1").value || "2025-01-01";
    const fecha2 = document.getElementById("fecha2").value || "2025-12-31";
    const tipos = getTiposSeleccionados();
  
    fetch("/geo", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        fecha1: fecha1,
        fecha2: fecha2,
        tipos: tipos
      })
    })
      .then(response => response.json())
      .then(data => {
        // Actualizamos el mapa si se reciben datos
        if (data && data.mapa) {
          const mapa = JSON.parse(data.mapa);
          Plotly.newPlot("mapa", mapa.data, mapa.layout, { responsive: true });
        }
        // Actualizamos el dropdown con la lista completa de tipos, manteniendo la selección actual
        if (data && data.tipos) {
          crearCheckboxes(data.tipos, tipos);
        }
        if(data && data.tabla_comunas){
          const tbody=document.querySelector("#tablaComunas tbody");
          tbody.innerHTML = "";
          data.tabla_comunas.forEach(fila => {
            const tr =document.createElement("tr");
            tr.innerHTML = `<td>${fila.comuna}</td><td>${fila.cantidad}</td>`;
            tbody.appendChild(tr);
          });
        }
        document.getElementById("spinner-overlay").style.display = "none";
      })
      .catch(error => {
        document.getElementById("spinner-overlay").style.display = "none";
        const mensajeError= document.getElementById("mensaje-error");
        mensajeError.style.display="block"
        mensajeError.textContent="Error al cargar los datos: "+ error.message;
        console.error("Error al actualizar el mapa: ", error);
      });
  }
  
  // Al cargar la página:
  document.addEventListener("DOMContentLoaded", function () {
    // Establecemos valores por defecto para las fechas
    const hoy= new Date();
    const inicioAño=`${hoy.getFullYear()}-01-01`;
    const finAño=`${hoy.getFullYear()}-12-31`;

    document.getElementById("fecha1").value = inicioAño;
    document.getElementById("fecha2").value = finAño;

    if(typeof MAPA_DATA!=='undefined'){
      const mapaParsed=typeof MAPA_DATA === 'string' ? JSON.parse(MAPA_DATA) : MAPA_DATA;
      Plotly.newPlot("mapa",mapaParsed.data, mapaParsed.layout, {responsive: true})
    }

    if(typeof TIPOS_INFRACCION !=="undefined"){
      crearCheckboxes(TIPOS_INFRACCION);
    }

    document.getElementById("spinner-overlay").style.display="none";
  
    // Manejar el envío del formulario de filtros
    document.getElementById("formGeo").addEventListener("submit", function (e) {
      e.preventDefault();
      const fecha1=document.getElementById("fecha1").value;
      const fecha2=document.getElementById("fecha2").value;

      if (new Date(fecha1) > new Date(fecha2)) {
        alert("La fecha inicial no puede ser posterior a la fecha final.");
        return;
      }

      actualizarMapa();
    });
  });
  
  // Actualización automática cada 5 minutos (300000 ms)
  setInterval(actualizarMapa, 300000);
  