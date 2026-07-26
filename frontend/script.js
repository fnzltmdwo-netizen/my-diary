const API_URL =
    "/api";

let currentDate =
    new Date();


let calendarDate =
    new Date(
        currentDate.getFullYear(),
        currentDate.getMonth(),
        1
    );


let noteTimer =
    null;


let editingScheduleId =
    null;


let editingTodoId =
    null;


// ======================================================
// 카테고리 / 반복 정보
// ======================================================

const CATEGORY_INFO = {

    daily: {
        icon: "🌿",
        name: "일상"
    },

    study: {
        icon: "📚",
        name: "공부"
    },

    exercise: {
        icon: "🏃",
        name: "운동"
    },

    appointment: {
        icon: "💕",
        name: "약속"
    },

    work: {
        icon: "💼",
        name: "업무"
    },

    etc: {
        icon: "✨",
        name: "기타"
    }

};


const REPEAT_INFO = {

    none: "",

    daily:
        "매일",

    weekly:
        "매주",

    monthly:
        "매월"

};


function getCategoryInfo(
    category
) {

    return (
        CATEGORY_INFO[category]
        ||
        CATEGORY_INFO.daily
    );

}


// ======================================================
// 요소
// ======================================================

const diaryPage =
    document.querySelector(
        ".diary-page"
    );


const calendarPage =
    document.getElementById(
        "calendarPage"
    );


const searchPage =
    document.getElementById(
        "searchPage"
    );


const todayNavBtn =
    document.getElementById(
        "todayNavBtn"
    );


const calendarNavBtn =
    document.getElementById(
        "calendarNavBtn"
    );


const searchNavBtn =
    document.getElementById(
        "searchNavBtn"
    );


const scheduleModal =
    document.getElementById(
        "scheduleModal"
    );


const todoModal =
    document.getElementById(
        "todoModal"
    );


const editScheduleModal =
    document.getElementById(
        "editScheduleModal"
    );


const editTodoModal =
    document.getElementById(
        "editTodoModal"
    );


// ======================================================
// 날짜
// ======================================================

function getDateKey() {

    const year =
        currentDate.getFullYear();


    const month =
        String(
            currentDate.getMonth() + 1
        ).padStart(
            2,
            "0"
        );


    const day =
        String(
            currentDate.getDate()
        ).padStart(
            2,
            "0"
        );


    return `${year}-${month}-${day}`;

}


function makeDateKey(
    year,
    month,
    day
) {

    return (
        `${year}-`
        +
        `${String(month).padStart(2, "0")}-`
        +
        `${String(day).padStart(2, "0")}`
    );

}


function updateDateDisplay() {

    document
        .getElementById(
            "dayText"
        )
        .innerText =
        currentDate.getDate();


    document
        .querySelector(
            ".month-text"
        )
        .innerText =
        currentDate
            .toLocaleDateString(
                "en-US",
                {
                    month:
                        "long"
                }
            )
            .toUpperCase();


    document
        .getElementById(
            "weekdayText"
        )
        .innerText =
        currentDate
            .toLocaleDateString(
                "en-US",
                {
                    weekday:
                        "long"
                }
            )
            .toUpperCase();


    loadCurrentDateData();

}


// ======================================================
// 화면
// ======================================================

function clearNavActive() {

    [
        todayNavBtn,
        calendarNavBtn,
        searchNavBtn
    ].forEach(
        button => {

            button.classList.remove(
                "active"
            );

        }
    );

}


function hideAllPages() {

    diaryPage.classList.add(
        "hidden"
    );


    calendarPage.classList.add(
        "hidden"
    );


    searchPage.classList.add(
        "hidden"
    );

}


function showDiaryPage() {

    hideAllPages();

    clearNavActive();


    diaryPage.classList.remove(
        "hidden"
    );


    todayNavBtn.classList.add(
        "active"
    );

}


function showCalendarPage() {

    hideAllPages();

    clearNavActive();


    calendarPage.classList.remove(
        "hidden"
    );


    calendarNavBtn.classList.add(
        "active"
    );


    calendarDate =
        new Date(
            currentDate.getFullYear(),
            currentDate.getMonth(),
            1
        );


    renderCalendar();

}


function showSearchPage() {

    hideAllPages();

    clearNavActive();


    searchPage.classList.remove(
        "hidden"
    );


    searchNavBtn.classList.add(
        "active"
    );


    setTimeout(
        () => {

            document
                .getElementById(
                    "searchInput"
                )
                .focus();

        },
        100
    );

}


// ======================================================
// 모달
// ======================================================

function openModal(
    modal
) {

    modal.classList.remove(
        "hidden"
    );

}


function closeModal(
    modal
) {

    modal.classList.add(
        "hidden"
    );

}


// ======================================================
// 반복 종료일 표시
// ======================================================

function updateRepeatUntilVisibility(
    editing = false
) {

    const select =
        document.getElementById(
            editing
                ? "editScheduleRepeatInput"
                : "scheduleRepeatInput"
        );


    const area =
        document.getElementById(
            editing
                ? "editScheduleRepeatUntilArea"
                : "scheduleRepeatUntilArea"
        );


    if (
        select.value === "none"
    ) {

        area.classList.add(
            "hidden"
        );

    }

    else {

        area.classList.remove(
            "hidden"
        );

    }

}


// ======================================================
// 날짜 데이터 불러오기
// ======================================================

async function loadCurrentDateData() {

    await Promise.all([
        loadSchedules(),
        loadTodos(),
        loadNote()
    ]);

}


// ======================================================
// 일정 불러오기
// ======================================================

async function loadSchedules() {

    try {

        const response =
            await fetch(
                `${API_URL}/schedules?date=${getDateKey()}`
            );


        if (!response.ok) {

            throw new Error(
                "일정 불러오기 실패"
            );

        }


        const schedules =
            await response.json();


        const scheduleList =
            document.getElementById(
                "scheduleList"
            );


        scheduleList.innerHTML =
            "";


        schedules.forEach(
            schedule => {

                const category =
                    schedule.category
                    ||
                    "daily";


                const categoryInfo =
                    getCategoryInfo(
                        category
                    );


                const repeatType =
                    schedule.repeat_type
                    ||
                    "none";


                const item =
                    document.createElement(
                        "div"
                    );


                item.className =
                    "schedule-item";


                if (
                    schedule.important
                ) {

                    item.classList.add(
                        "important"
                    );

                }


                item.innerHTML = `
                    <span
                        class="schedule-time"
                    >
                        ${schedule.time}
                    </span>


                    <label
                        class="schedule-content"
                    >

                        <input
                            type="checkbox"
                            ${
                                schedule.completed
                                    ? "checked"
                                    : ""
                            }
                        >


                        <div
                            class="schedule-main"
                        >

                            ${
                                schedule.important
                                    ? `
                                        <span
                                            class="important-star"
                                        >
                                            ⭐
                                        </span>
                                    `
                                    : ""
                            }


                            <span
                                class="
                                    category-badge
                                    category-${category}
                                "
                            >
                                ${categoryInfo.icon}
                                ${categoryInfo.name}
                            </span>


                            ${
                                repeatType !== "none"
                                    ? `
                                        <span
                                            class="repeat-badge"
                                        >
                                            🔁
                                            ${REPEAT_INFO[repeatType]}
                                        </span>
                                    `
                                    : ""
                            }


                            <span
                                class="schedule-text"
                            ></span>

                        </div>

                    </label>


                    <div
                        class="item-actions"
                    >

                        <button
                            type="button"
                            class="
                                item-action-button
                                edit-schedule-button
                            "
                            title="수정"
                        >
                            ✏️
                        </button>


                        <button
                            type="button"
                            class="
                                item-action-button
                                delete-button
                                delete-schedule-button
                            "
                            title="삭제"
                        >
                            🗑️
                        </button>

                    </div>
                `;


                item
                    .querySelector(
                        ".schedule-text"
                    )
                    .textContent =
                    schedule.text;


                const checkbox =
                    item.querySelector(
                        'input[type="checkbox"]'
                    );


                checkbox.addEventListener(
                    "change",
                    async () => {

                        await toggleSchedule(
                            schedule.id,
                            checkbox.checked
                        );

                    }
                );


                item
                    .querySelector(
                        ".edit-schedule-button"
                    )
                    .addEventListener(
                        "click",
                        () => {

                            openEditSchedule(
                                schedule
                            );

                        }
                    );


                item
                    .querySelector(
                        ".delete-schedule-button"
                    )
                    .addEventListener(
                        "click",
                        async () => {

                            await deleteSchedule(
                                schedule.id,
                                repeatType
                            );

                        }
                    );


                scheduleList.appendChild(
                    item
                );

            }
        );

    }

    catch (error) {

        console.error(
            error
        );

    }

}


// ======================================================
// 일정 추가
// ======================================================

async function addSchedule() {

    const timeInput =
        document.getElementById(
            "scheduleTimeInput"
        );


    const textInput =
        document.getElementById(
            "scheduleTextInput"
        );


    const categoryInput =
        document.getElementById(
            "scheduleCategoryInput"
        );


    const importantInput =
        document.getElementById(
            "scheduleImportantInput"
        );


    const repeatInput =
        document.getElementById(
            "scheduleRepeatInput"
        );


    const repeatUntilInput =
        document.getElementById(
            "scheduleRepeatUntilInput"
        );


    const time =
        timeInput.value;


    const text =
        textInput.value.trim();


    const category =
        categoryInput.value;


    const important =
        importantInput.checked;


    const repeatType =
        repeatInput.value;


    let repeatUntil =
        repeatUntilInput.value;


    if (
        time === ""
        ||
        text === ""
    ) {

        alert(
            "시간과 일정 내용을 입력해주세요."
        );

        return;

    }


    if (
        repeatType === "none"
    ) {

        repeatUntil =
            null;

    }


    if (
        repeatUntil
        &&
        repeatUntil < getDateKey()
    ) {

        alert(
            "반복 종료일은 일정 시작일보다 빠를 수 없어요."
        );

        return;

    }


    try {

        const response =
            await fetch(
                `${API_URL}/schedules`,
                {
                    method:
                        "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({
                            date:
                                getDateKey(),

                            time:
                                time,

                            text:
                                text,

                            category:
                                category,

                            important:
                                important,

                            repeat_type:
                                repeatType,

                            repeat_until:
                                repeatUntil
                        })
                }
            );


        if (!response.ok) {

            const data =
                await response.json()
                    .catch(
                        () => ({})
                    );


            throw new Error(
                data.detail
                ||
                "일정 저장 실패"
            );

        }


        timeInput.value =
            "";


        textInput.value =
            "";


        categoryInput.value =
            "daily";


        importantInput.checked =
            false;


        repeatInput.value =
            "none";


        repeatUntilInput.value =
            "";


        updateRepeatUntilVisibility(
            false
        );


        closeModal(
            scheduleModal
        );


        await loadSchedules();

    }

    catch (error) {

        console.error(
            error
        );


        alert(
            error.message
            ||
            "일정 저장에 실패했습니다."
        );

    }

}


// ======================================================
// 일정 완료
// ======================================================

async function toggleSchedule(
    id,
    completed
) {

    try {

        const response =
            await fetch(
                `${API_URL}/schedules/${id}/complete`,
                {
                    method:
                        "PATCH",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({
                            completed:
                                completed,

                            date:
                                getDateKey()
                        })
                }
            );


        if (!response.ok) {

            throw new Error(
                "완료 상태 저장 실패"
            );

        }

    }

    catch (error) {

        console.error(
            error
        );


        alert(
            "완료 상태 저장에 실패했습니다."
        );


        await loadSchedules();

    }

}


// ======================================================
// 일정 수정
// ======================================================

function openEditSchedule(
    schedule
) {

    editingScheduleId =
        schedule.id;


    document
        .getElementById(
            "editScheduleTimeInput"
        )
        .value =
        schedule.time;


    document
        .getElementById(
            "editScheduleTextInput"
        )
        .value =
        schedule.text;


    document
        .getElementById(
            "editScheduleCategoryInput"
        )
        .value =
        schedule.category
        ||
        "daily";


    document
        .getElementById(
            "editScheduleImportantInput"
        )
        .checked =
        Boolean(
            schedule.important
        );


    document
        .getElementById(
            "editScheduleRepeatInput"
        )
        .value =
        schedule.repeat_type
        ||
        "none";


    document
        .getElementById(
            "editScheduleRepeatUntilInput"
        )
        .value =
        schedule.repeat_until
        ||
        "";


    updateRepeatUntilVisibility(
        true
    );


    openModal(
        editScheduleModal
    );

}


async function saveEditSchedule() {

    if (
        editingScheduleId === null
    ) {

        return;

    }


    const time =
        document
            .getElementById(
                "editScheduleTimeInput"
            )
            .value;


    const text =
        document
            .getElementById(
                "editScheduleTextInput"
            )
            .value
            .trim();


    const category =
        document
            .getElementById(
                "editScheduleCategoryInput"
            )
            .value;


    const important =
        document
            .getElementById(
                "editScheduleImportantInput"
            )
            .checked;


    const repeatType =
        document
            .getElementById(
                "editScheduleRepeatInput"
            )
            .value;


    let repeatUntil =
        document
            .getElementById(
                "editScheduleRepeatUntilInput"
            )
            .value;


    if (
        time === ""
        ||
        text === ""
    ) {

        alert(
            "시간과 일정 내용을 입력해주세요."
        );

        return;

    }


    if (
        repeatType === "none"
    ) {

        repeatUntil =
            null;

    }


    try {

        const response =
            await fetch(
                `${API_URL}/schedules/${editingScheduleId}`,
                {
                    method:
                        "PATCH",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({
                            time:
                                time,

                            text:
                                text,

                            category:
                                category,

                            important:
                                important,

                            repeat_type:
                                repeatType,

                            repeat_until:
                                repeatUntil
                        })
                }
            );


        if (!response.ok) {

            const data =
                await response.json()
                    .catch(
                        () => ({})
                    );


            throw new Error(
                data.detail
                ||
                "일정 수정 실패"
            );

        }


        editingScheduleId =
            null;


        closeModal(
            editScheduleModal
        );


        await loadSchedules();

    }

    catch (error) {

        console.error(
            error
        );


        alert(
            error.message
            ||
            "일정 수정에 실패했습니다."
        );

    }

}


// ======================================================
// 일정 삭제
// ======================================================

async function deleteSchedule(
    id,
    repeatType
) {

    let message =
        "이 일정을 삭제할까?";


    if (
        repeatType !== "none"
    ) {

        message =
            "이 반복 일정을 전체 삭제할까?";

    }


    if (
        !confirm(message)
    ) {

        return;

    }


    try {

        const response =
            await fetch(
                `${API_URL}/schedules/${id}`,
                {
                    method:
                        "DELETE"
                }
            );


        if (!response.ok) {

            throw new Error(
                "일정 삭제 실패"
            );

        }


        await loadSchedules();

    }

    catch (error) {

        console.error(
            error
        );


        alert(
            "일정 삭제에 실패했습니다."
        );

    }

}


// ======================================================
// TODO 불러오기
// ======================================================

async function loadTodos() {

    try {

        const response =
            await fetch(
                `${API_URL}/todos?date=${getDateKey()}`
            );


        if (!response.ok) {

            throw new Error(
                "할 일 불러오기 실패"
            );

        }


        const todos =
            await response.json();


        const todoList =
            document.getElementById(
                "todoList"
            );


        todoList.innerHTML =
            "";


        todos.forEach(
            todo => {

                const item =
                    document.createElement(
                        "div"
                    );


                item.className =
                    "todo-item";


                item.innerHTML = `
                    <input
                        type="checkbox"
                        ${
                            todo.completed
                                ? "checked"
                                : ""
                        }
                    >

                    <span
                        class="todo-text"
                    ></span>


                    <div
                        class="item-actions"
                    >

                        <button
                            type="button"
                            class="
                                item-action-button
                                edit-todo-button
                            "
                            title="수정"
                        >
                            ✏️
                        </button>


                        <button
                            type="button"
                            class="
                                item-action-button
                                delete-button
                                delete-todo-button
                            "
                            title="삭제"
                        >
                            🗑️
                        </button>

                    </div>
                `;


                item
                    .querySelector(
                        ".todo-text"
                    )
                    .textContent =
                    todo.text;


                const checkbox =
                    item.querySelector(
                        'input[type="checkbox"]'
                    );


                checkbox.addEventListener(
                    "change",
                    async () => {

                        await toggleTodo(
                            todo.id,
                            checkbox.checked
                        );

                    }
                );


                item
                    .querySelector(
                        ".edit-todo-button"
                    )
                    .addEventListener(
                        "click",
                        () => {

                            openEditTodo(
                                todo
                            );

                        }
                    );


                item
                    .querySelector(
                        ".delete-todo-button"
                    )
                    .addEventListener(
                        "click",
                        async () => {

                            await deleteTodo(
                                todo.id
                            );

                        }
                    );


                todoList.appendChild(
                    item
                );

            }
        );

    }

    catch (error) {

        console.error(
            error
        );

    }

}


// ======================================================
// TODO 추가
// ======================================================

async function addTodo() {

    const input =
        document.getElementById(
            "todoTextInput"
        );


    const text =
        input.value.trim();


    if (
        text === ""
    ) {

        alert(
            "할 일을 입력해주세요."
        );

        return;

    }


    try {

        const response =
            await fetch(
                `${API_URL}/todos`,
                {
                    method:
                        "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({
                            date:
                                getDateKey(),

                            text:
                                text
                        })
                }
            );


        if (!response.ok) {

            throw new Error(
                "할 일 저장 실패"
            );

        }


        input.value =
            "";


        closeModal(
            todoModal
        );


        await loadTodos();

    }

    catch (error) {

        console.error(
            error
        );


        alert(
            "할 일 저장에 실패했습니다."
        );

    }

}


// ======================================================
// TODO 완료
// ======================================================

async function toggleTodo(
    id,
    completed
) {

    try {

        const response =
            await fetch(
                `${API_URL}/todos/${id}/complete`,
                {
                    method:
                        "PATCH",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({
                            completed:
                                completed
                        })
                }
            );


        if (!response.ok) {

            throw new Error(
                "TODO 완료 저장 실패"
            );

        }

    }

    catch (error) {

        console.error(
            error
        );


        await loadTodos();

    }

}


// ======================================================
// TODO 수정
// ======================================================

function openEditTodo(
    todo
) {

    editingTodoId =
        todo.id;


    document
        .getElementById(
            "editTodoTextInput"
        )
        .value =
        todo.text;


    openModal(
        editTodoModal
    );

}


async function saveEditTodo() {

    if (
        editingTodoId === null
    ) {

        return;

    }


    const text =
        document
            .getElementById(
                "editTodoTextInput"
            )
            .value
            .trim();


    if (
        text === ""
    ) {

        alert(
            "할 일을 입력해주세요."
        );

        return;

    }


    try {

        const response =
            await fetch(
                `${API_URL}/todos/${editingTodoId}`,
                {
                    method:
                        "PATCH",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({
                            text:
                                text
                        })
                }
            );


        if (!response.ok) {

            throw new Error(
                "할 일 수정 실패"
            );

        }


        editingTodoId =
            null;


        closeModal(
            editTodoModal
        );


        await loadTodos();

    }

    catch (error) {

        console.error(
            error
        );


        alert(
            "할 일 수정에 실패했습니다."
        );

    }

}


// ======================================================
// TODO 삭제
// ======================================================

async function deleteTodo(
    id
) {

    if (
        !confirm(
            "이 할 일을 삭제할까?"
        )
    ) {

        return;

    }


    try {

        const response =
            await fetch(
                `${API_URL}/todos/${id}`,
                {
                    method:
                        "DELETE"
                }
            );


        if (!response.ok) {

            throw new Error(
                "TODO 삭제 실패"
            );

        }


        await loadTodos();

    }

    catch (error) {

        console.error(
            error
        );


        alert(
            "할 일 삭제에 실패했습니다."
        );

    }

}


// ======================================================
// 메모
// ======================================================

async function loadNote() {

    try {

        const response =
            await fetch(
                `${API_URL}/note?date=${getDateKey()}`
            );


        if (!response.ok) {

            throw new Error(
                "메모 불러오기 실패"
            );

        }


        const note =
            await response.json();


        document
            .getElementById(
                "dailyNote"
            )
            .value =
            note.text
            ||
            "";

    }

    catch (error) {

        console.error(
            error
        );

    }

}


async function saveNote() {

    const text =
        document
            .getElementById(
                "dailyNote"
            )
            .value;


    try {

        await fetch(
            `${API_URL}/note`,
            {
                method:
                    "PUT",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body:
                    JSON.stringify({
                        date:
                            getDateKey(),

                        text:
                            text
                    })
            }
        );

    }

    catch (error) {

        console.error(
            error
        );

    }

}


// ======================================================
// 달력
// ======================================================

async function renderCalendar() {

    const year =
        calendarDate.getFullYear();


    const monthIndex =
        calendarDate.getMonth();


    const month =
        monthIndex + 1;


    document
        .getElementById(
            "calendarYear"
        )
        .innerText =
        year;


    document
        .getElementById(
            "calendarMonth"
        )
        .innerText =
        calendarDate
            .toLocaleDateString(
                "en-US",
                {
                    month:
                        "long"
                }
            )
            .toUpperCase();


    const grid =
        document.getElementById(
            "calendarGrid"
        );


    grid.innerHTML =
        "";


    const firstDay =
        new Date(
            year,
            monthIndex,
            1
        )
        .getDay();


    const lastDate =
        new Date(
            year,
            monthIndex + 1,
            0
        )
        .getDate();


    let monthData =
        {};


    try {

        const response =
            await fetch(
                `${API_URL}/calendar?year=${year}&month=${month}`
            );


        if (!response.ok) {

            throw new Error(
                "달력 데이터 실패"
            );

        }


        monthData =
            await response.json();

    }

    catch (error) {

        console.error(
            error
        );

    }


    for (
        let i = 0;
        i < firstDay;
        i++
    ) {

        const empty =
            document.createElement(
                "div"
            );


        empty.className =
            "calendar-day empty";


        grid.appendChild(
            empty
        );

    }


    const now =
        new Date();


    const todayKey =
        makeDateKey(
            now.getFullYear(),
            now.getMonth() + 1,
            now.getDate()
        );


    for (
        let day = 1;
        day <= lastDate;
        day++
    ) {

        const dateKey =
            makeDateKey(
                year,
                month,
                day
            );


        const cell =
            document.createElement(
                "div"
            );


        cell.className =
            "calendar-day";


        if (
            dateKey === todayKey
        ) {

            cell.classList.add(
                "today"
            );

        }


        if (
            dateKey === getDateKey()
        ) {

            cell.classList.add(
                "selected"
            );

        }


        const number =
            document.createElement(
                "span"
            );


        number.className =
            "calendar-day-number";


        number.innerText =
            day;


        cell.appendChild(
            number
        );


        const data =
            monthData[dateKey];


        if (data) {

            if (
                data.important_count > 0
            ) {

                const star =
                    document.createElement(
                        "span"
                    );


                star.className =
                    "calendar-important-star";


                star.innerText =
                    "⭐";


                cell.appendChild(
                    star
                );

            }


            const dotArea =
                document.createElement(
                    "div"
                );


            dotArea.className =
                "calendar-dot-area";


            if (
                data.schedule_count > 0
            ) {

                const dot =
                    document.createElement(
                        "span"
                    );


                dot.className =
                    "calendar-dot";


                dotArea.appendChild(
                    dot
                );

            }


            if (
                data.todo_count > 0
            ) {

                const dot =
                    document.createElement(
                        "span"
                    );


                dot.className =
                    "calendar-dot todo";


                dotArea.appendChild(
                    dot
                );

            }


            cell.appendChild(
                dotArea
            );

        }


        cell.addEventListener(
            "click",
            () => {

                currentDate =
                    new Date(
                        year,
                        monthIndex,
                        day
                    );


                updateDateDisplay();


                showDiaryPage();

            }
        );


        grid.appendChild(
            cell
        );

    }

}


// ======================================================
// 검색
// ======================================================

async function searchDiary() {

    const keyword =
        document
            .getElementById(
                "searchInput"
            )
            .value
            .trim();


    const info =
        document.getElementById(
            "searchInfo"
        );


    const resultsBox =
        document.getElementById(
            "searchResults"
        );


    if (
        keyword === ""
    ) {

        info.innerText =
            "검색어를 입력해주세요.";


        resultsBox.innerHTML =
            "";


        return;

    }


    info.innerText =
        "검색 중...";


    resultsBox.innerHTML =
        "";


    try {

        const response =
            await fetch(
                `${API_URL}/search?q=${encodeURIComponent(keyword)}`
            );


        if (!response.ok) {

            throw new Error(
                "검색 실패"
            );

        }


        const results =
            await response.json();


        info.innerText =
            `"${keyword}" 검색 결과 ${results.length}개`;


        if (
            results.length === 0
        ) {

            resultsBox.innerHTML = `
                <div
                    class="search-empty"
                >
                    검색 결과가 없어요 🥲
                </div>
            `;


            return;

        }


        results.forEach(
            result => {

                const item =
                    document.createElement(
                        "button"
                    );


                item.type =
                    "button";


                item.className =
                    "search-result-item";


                let typeIcon =
                    "📅";


                let typeName =
                    "일정";


                if (
                    result.type === "todo"
                ) {

                    typeIcon =
                        "☑️";


                    typeName =
                        "할 일";

                }


                if (
                    result.type === "note"
                ) {

                    typeIcon =
                        "📝";


                    typeName =
                        "메모";

                }


                let categoryText =
                    "";


                if (
                    result.type ===
                    "schedule"
                ) {

                    const info =
                        getCategoryInfo(
                            result.category
                        );


                    categoryText =
                        info.icon;

                }


                let repeatText =
                    "";


                if (
                    result.repeat_type
                    &&
                    result.repeat_type !==
                    "none"
                ) {

                    repeatText =
                        `🔁 ${REPEAT_INFO[result.repeat_type]}`;

                }


                item.innerHTML = `
                    <div
                        class="search-result-top"
                    >

                        <span
                            class="search-result-date"
                        >
                            ${formatDate(result.date)}
                        </span>


                        <span
                            class="search-result-type"
                        >
                            ${typeIcon}
                            ${typeName}
                        </span>

                    </div>


                    <div
                        class="
                            search-result-text
                            ${
                                result.completed
                                    ? "search-result-completed"
                                    : ""
                            }
                        "
                    >

                        ${
                            result.important
                                ? "⭐ "
                                : ""
                        }


                        ${
                            categoryText
                                ? `
                                    <span
                                        class="search-category"
                                    >
                                        ${categoryText}
                                    </span>
                                `
                                : ""
                        }


                        ${
                            repeatText
                                ? `
                                    <span
                                        class="search-repeat"
                                    >
                                        ${repeatText}
                                    </span>
                                `
                                : ""
                        }


                        ${
                            result.time
                                ? `
                                    <span
                                        class="search-result-time"
                                    >
                                        ${result.time}
                                    </span>
                                `
                                : ""
                        }


                        <span
                            class="result-content"
                        ></span>

                    </div>
                `;


                let displayText =
                    result.text;


                if (
                    result.type === "note"
                    &&
                    displayText.length > 100
                ) {

                    displayText =
                        displayText.substring(
                            0,
                            100
                        )
                        +
                        "…";

                }


                item
                    .querySelector(
                        ".result-content"
                    )
                    .textContent =
                    displayText;


                item.addEventListener(
                    "click",
                    () => {

                        openSearchResult(
                            result.date
                        );

                    }
                );


                resultsBox.appendChild(
                    item
                );

            }
        );

    }

    catch (error) {

        console.error(
            error
        );


        info.innerText =
            "검색 중 오류가 발생했습니다.";

    }

}


function formatDate(
    dateString
) {

    const [
        year,
        month,
        day
    ] =
        dateString.split("-");


    return (
        `${year}.${month}.${day}`
    );

}


function openSearchResult(
    dateString
) {

    const [
        year,
        month,
        day
    ] =
        dateString
            .split("-")
            .map(Number);


    currentDate =
        new Date(
            year,
            month - 1,
            day
        );


    updateDateDisplay();


    showDiaryPage();

}


// ======================================================
// 날짜 이동
// ======================================================

document
    .getElementById(
        "prevDayBtn"
    )
    .addEventListener(
        "click",
        () => {

            currentDate.setDate(
                currentDate.getDate()
                - 1
            );


            updateDateDisplay();

        }
    );


document
    .getElementById(
        "nextDayBtn"
    )
    .addEventListener(
        "click",
        () => {

            currentDate.setDate(
                currentDate.getDate()
                + 1
            );


            updateDateDisplay();

        }
    );


// ======================================================
// 월 이동
// ======================================================

document
    .getElementById(
        "prevMonthBtn"
    )
    .addEventListener(
        "click",
        () => {

            calendarDate.setMonth(
                calendarDate.getMonth()
                - 1
            );


            renderCalendar();

        }
    );


document
    .getElementById(
        "nextMonthBtn"
    )
    .addEventListener(
        "click",
        () => {

            calendarDate.setMonth(
                calendarDate.getMonth()
                + 1
            );


            renderCalendar();

        }
    );


// ======================================================
// 하단 메뉴
// ======================================================

todayNavBtn.addEventListener(
    "click",
    () => {

        currentDate =
            new Date();


        updateDateDisplay();


        showDiaryPage();

    }
);


calendarNavBtn.addEventListener(
    "click",
    showCalendarPage
);


searchNavBtn.addEventListener(
    "click",
    showSearchPage
);


document
    .getElementById(
        "settingsNavBtn"
    )
    .addEventListener(
        "click",
        async () => {

            const confirmed =
                confirm(
                    "로그아웃할까?"
                );


            if (!confirmed) {

                return;

            }


            await fetch(
                "/api/logout",
                {
                    method:
                        "POST"
                }
            );


            window.location.href =
                "/";

        }
    );


// ======================================================
// 검색
// ======================================================

document
    .getElementById(
        "searchBtn"
    )
    .addEventListener(
        "click",
        searchDiary
    );


document
    .getElementById(
        "searchInput"
    )
    .addEventListener(
        "keydown",
        event => {

            if (
                event.key ===
                "Enter"
            ) {

                searchDiary();

            }

        }
    );


// ======================================================
// 일정 / TODO 추가
// ======================================================

document
    .getElementById(
        "addScheduleBtn"
    )
    .addEventListener(
        "click",
        () => {

            openModal(
                scheduleModal
            );

        }
    );


document
    .getElementById(
        "quickAddBtn"
    )
    .addEventListener(
        "click",
        () => {

            openModal(
                scheduleModal
            );

        }
    );


document
    .getElementById(
        "addTodoBtn"
    )
    .addEventListener(
        "click",
        () => {

            openModal(
                todoModal
            );

        }
    );


document
    .getElementById(
        "saveScheduleBtn"
    )
    .addEventListener(
        "click",
        addSchedule
    );


document
    .getElementById(
        "saveTodoBtn"
    )
    .addEventListener(
        "click",
        addTodo
    );


// ======================================================
// 수정 저장
// ======================================================

document
    .getElementById(
        "saveEditScheduleBtn"
    )
    .addEventListener(
        "click",
        saveEditSchedule
    );


document
    .getElementById(
        "saveEditTodoBtn"
    )
    .addEventListener(
        "click",
        saveEditTodo
    );


// ======================================================
// 반복 선택
// ======================================================

document
    .getElementById(
        "scheduleRepeatInput"
    )
    .addEventListener(
        "change",
        () => {

            updateRepeatUntilVisibility(
                false
            );

        }
    );


document
    .getElementById(
        "editScheduleRepeatInput"
    )
    .addEventListener(
        "change",
        () => {

            updateRepeatUntilVisibility(
                true
            );

        }
    );


// ======================================================
// 모달 닫기
// ======================================================

document
    .getElementById(
        "closeScheduleModal"
    )
    .addEventListener(
        "click",
        () => {

            closeModal(
                scheduleModal
            );

        }
    );


document
    .getElementById(
        "closeTodoModal"
    )
    .addEventListener(
        "click",
        () => {

            closeModal(
                todoModal
            );

        }
    );


document
    .getElementById(
        "closeEditScheduleModal"
    )
    .addEventListener(
        "click",
        () => {

            editingScheduleId =
                null;


            closeModal(
                editScheduleModal
            );

        }
    );


document
    .getElementById(
        "closeEditTodoModal"
    )
    .addEventListener(
        "click",
        () => {

            editingTodoId =
                null;


            closeModal(
                editTodoModal
            );

        }
    );


[
    scheduleModal,
    todoModal,
    editScheduleModal,
    editTodoModal
]
.forEach(
    modal => {

        modal.addEventListener(
            "click",
            event => {

                if (
                    event.target === modal
                ) {

                    closeModal(
                        modal
                    );

                }

            }
        );

    }
);


// ======================================================
// 메모 자동 저장
// ======================================================

document
    .getElementById(
        "dailyNote"
    )
    .addEventListener(
        "input",
        () => {

            clearTimeout(
                noteTimer
            );


            noteTimer =
                setTimeout(
                    saveNote,
                    500
                );

        }
    );


// ======================================================
// 시작
// ======================================================

updateRepeatUntilVisibility(
    false
);


updateRepeatUntilVisibility(
    true
);


updateDateDisplay();


showDiaryPage();