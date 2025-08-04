// apps/profiles/js/profile.js

document.addEventListener('DOMContentLoaded', function () {
  const universitySelect = document.getElementById('university');
  const majorSelect = document.getElementById('major');

  if (universitySelect && majorSelect) {
    universitySelect.addEventListener('change', function () {
      const selectedUniversity = this.value;

      fetch(`/profiles/api/majors/?school_name=${encodeURIComponent(selectedUniversity)}`)
        .then(response => response.json())
        .then(data => {
          // 초기화
          majorSelect.innerHTML = '<option selected disabled value="">전공하시는 학과를 선택해주세요</option>';
          // 새 학과 옵션 채우기
          data.majors.forEach(major => {
            const option = document.createElement('option');
            option.value = major;
            option.textContent = major;
            majorSelect.appendChild(option);
          });
        })
        .catch(error => {
          console.error('학과 불러오기 실패:', error);
        });
    });
  }
});
