
document.getElementById('room_id').addEventListener('change', function() {
    var roomId = this.value;
    var equipmentSelect = document.getElementById('equipment_id');

    // Clear the PC dropdown before fetching new options
    equipmentSelect.innerHTML = '<option disabled selected>Loading PCs...</option>';

    fetch(`/admin/rooms/${roomId}/available_pcs`)
        .then(response => response.json())
        .then(data => {
            equipmentSelect.innerHTML = ''; // Clear options
            if (data.length === 0) {
                equipmentSelect.innerHTML = '<option disabled selected>No PCs available</option>';
            } else {
                data.forEach(pc => {
                    let option = document.createElement('option');
                    option.value = pc.id;
                    option.textContent = pc.name;
                    equipmentSelect.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('Error fetching PCs:', error);
            equipmentSelect.innerHTML = '<option disabled selected>Error loading PCs</option>';
        });
});

